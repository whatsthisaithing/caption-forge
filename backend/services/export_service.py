"""Export service for dataset exports."""

import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from ..config import get_settings, PROJECT_ROOT
from ..models import Dataset, DatasetFile, CaptionSet, Caption, ExportHistory, TrackedFile
from ..schemas import ExportRequest
from .thumbnail_service import ThumbnailService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting datasets."""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.staging_dir = PROJECT_ROOT / self.settings.export.staging_path
        self.staging_dir.mkdir(parents=True, exist_ok=True)
    
    async def start_export(self, dataset_id: str, request: ExportRequest) -> dict:
        """Start exporting a dataset."""
        # Verify dataset exists
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        # Verify caption set exists
        caption_set = self.db.query(CaptionSet).filter(
            CaptionSet.id == request.caption_set_id
        ).first()
        if not caption_set:
            raise ValueError(f"Caption set not found: {request.caption_set_id}")
        
        # Validate export path for folder exports
        if request.export_type == "folder":
            if not request.export_path:
                raise ValueError("Export path is required for folder exports")
            export_path = Path(request.export_path)
            export_path.mkdir(parents=True, exist_ok=True)
        else:
            # ZIP export - use staging directory
            export_path = self.staging_dir / f"{dataset.slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Get files to export
        query = self.db.query(DatasetFile).filter(
            DatasetFile.dataset_id == dataset_id,
            DatasetFile.excluded == False
        )
        
        # Apply quality filter
        if request.min_quality_score is not None:
            query = query.filter(DatasetFile.quality_score >= request.min_quality_score)
        
        # Apply flag filter
        if request.exclude_flagged:
            # This is simplified - real implementation would parse JSON flags
            pass
        
        dataset_files = query.order_by(DatasetFile.order_index).all()
        
        if not dataset_files:
            raise ValueError("No files to export after applying filters")
        
        # Create export history record
        export_record = ExportHistory(
            dataset_id=dataset_id,
            caption_set_id=request.caption_set_id,
            export_config=json.dumps(request.model_dump()),
            export_path=str(export_path),
            export_type=request.export_type,
            status="running"
        )
        self.db.add(export_record)
        self.db.commit()
        self.db.refresh(export_record)
        
        # Perform export
        try:
            if request.export_type == "folder":
                result = await self._export_to_folder(
                    export_record.id,
                    dataset_files,
                    caption_set,
                    export_path,
                    request
                )
            else:
                result = await self._export_to_zip(
                    export_record.id,
                    dataset_files,
                    caption_set,
                    export_path,
                    request
                )
            
            export_record.status = "completed"
            export_record.completed_date = datetime.utcnow()
            export_record.file_count = result["file_count"]
            export_record.total_size_bytes = result["total_size"]
            
        except Exception as e:
            logger.exception(f"Export failed: {e}")
            export_record.status = "failed"
            export_record.error_message = str(e)
            raise
        
        finally:
            self.db.commit()
        
        return {
            "export_id": export_record.id,
            "status": export_record.status,
            "export_path": str(export_path),
            "estimated_files": len(dataset_files),
            "estimated_size_mb": None
        }
    
    async def _export_to_folder(
        self,
        export_id: str,
        dataset_files: List[DatasetFile],
        caption_set: CaptionSet,
        export_path: Path,
        request: ExportRequest
    ) -> dict:
        """Export dataset to a folder."""
        file_count = 0
        total_size = 0
        
        for idx, df in enumerate(dataset_files):
            file = df.file
            source_path = Path(file.absolute_path)
            
            if not source_path.exists():
                logger.warning(f"Source file not found: {source_path}")
                continue
            
            # Generate numbered filename with optional prefix
            file_num = request.numbering_start + idx
            num_str = str(file_num).zfill(request.numbering_padding)
            
            # Add prefix if provided
            if request.filename_prefix:
                base_name = f"{request.filename_prefix}-{num_str}"
            else:
                base_name = num_str
            
            # Determine output format and extension
            if request.image_format == "original" or not request.image_format:
                ext = source_path.suffix
            else:
                ext = f".{request.image_format}" if request.image_format != "jpeg" else ".jpg"
            
            output_filename = f"{base_name}{ext}"
            output_path = export_path / output_filename
            
            # Process and copy image
            if request.image_format and request.image_format != "original":
                self._process_image(source_path, output_path, request)
            elif request.target_resolution or request.max_resolution_longest_side:
                self._process_image(source_path, output_path, request)
            else:
                shutil.copy2(source_path, output_path)
            
            total_size += output_path.stat().st_size
            
            # Write caption file
            caption = self.db.query(Caption).filter(
                Caption.caption_set_id == caption_set.id,
                Caption.file_id == file.id
            ).first()
            
            if caption:
                caption_filename = f"{base_name}.{request.caption_extension}"
                caption_path = export_path / caption_filename
                caption_path.write_text(caption.text, encoding="utf-8")
            
            file_count += 1
        
        # Write manifest if requested
        if request.include_manifest:
            self._write_manifest(export_path, dataset_files, caption_set, request)
        
        return {"file_count": file_count, "total_size": total_size}
    
    async def _export_to_zip(
        self,
        export_id: str,
        dataset_files: List[DatasetFile],
        caption_set: CaptionSet,
        zip_path: Path,
        request: ExportRequest
    ) -> dict:
        """Export dataset to a ZIP file."""
        file_count = 0
        total_size = 0
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, df in enumerate(dataset_files):
                file = df.file
                source_path = Path(file.absolute_path)
                
                if not source_path.exists():
                    logger.warning(f"Source file not found: {source_path}")
                    continue
                
                # Generate numbered filename with optional prefix
                file_num = request.numbering_start + idx
                num_str = str(file_num).zfill(request.numbering_padding)
                
                # Add prefix if provided
                if request.filename_prefix:
                    base_name = f"{request.filename_prefix}-{num_str}"
                else:
                    base_name = num_str
                
                # Determine output format and extension
                if request.image_format == "original" or not request.image_format:
                    ext = source_path.suffix
                else:
                    ext = f".{request.image_format}" if request.image_format != "jpeg" else ".jpg"
                
                output_filename = f"{base_name}{ext}"
                
                # Process image if needed
                if request.image_format and request.image_format != "original":
                    # Process to temp file then add to zip
                    temp_path = self.staging_dir / f"temp_{export_id}_{output_filename}"
                    self._process_image(source_path, temp_path, request)
                    zf.write(temp_path, output_filename)
                    total_size += temp_path.stat().st_size
                    temp_path.unlink()
                elif request.target_resolution or request.max_resolution_longest_side:
                    temp_path = self.staging_dir / f"temp_{export_id}_{output_filename}"
                    self._process_image(source_path, temp_path, request)
                    zf.write(temp_path, output_filename)
                    total_size += temp_path.stat().st_size
                    temp_path.unlink()
                else:
                    zf.write(source_path, output_filename)
                    total_size += source_path.stat().st_size
                
                # Write caption file
                caption = self.db.query(Caption).filter(
                    Caption.caption_set_id == caption_set.id,
                    Caption.file_id == file.id
                ).first()
                
                if caption:
                    caption_filename = f"{base_name}.{request.caption_extension}"
                    zf.writestr(caption_filename, caption.text)
                
                file_count += 1
            
            # Write manifest if requested
            if request.include_manifest:
                manifest = self._generate_manifest(dataset_files, caption_set, request)
                zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        
        return {"file_count": file_count, "total_size": total_size}
    
    def _process_image(self, source_path: Path, output_path: Path, request: ExportRequest):
        """Process an image (resize, convert format, strip metadata)."""
        from PIL import Image
        
        with Image.open(source_path) as img:
            # Convert mode if necessary
            output_format = request.image_format or source_path.suffix[1:].lower()
            if output_format in ("jpeg", "jpg") and img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA"):
                    background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Resize if needed
            # max_resolution_longest_side takes precedence over target_resolution
            resize_to = request.max_resolution_longest_side or request.target_resolution
            if resize_to:
                width, height = img.size
                max_dim = max(width, height)
                
                # Resize both up and down to match the target resolution
                if max_dim != resize_to:
                    scale = resize_to / max_dim
                    new_size = (int(width * scale), int(height * scale))
                    
                    # Use best quality resampling algorithm
                    # LANCZOS for downscaling, BICUBIC for upscaling
                    resampling = Image.Resampling.LANCZOS if scale < 1 else Image.Resampling.BICUBIC
                    img = img.resize(new_size, resampling)
            
            # Save with appropriate settings
            save_kwargs = {}
            if output_format in ("jpeg", "jpg"):
                save_kwargs["quality"] = request.jpeg_quality
                save_kwargs["optimize"] = True
                if request.strip_metadata:
                    save_kwargs["exif"] = b""
                img.save(output_path, format="JPEG", **save_kwargs)
            elif output_format == "png":
                save_kwargs["compress_level"] = request.png_compression
                save_kwargs["optimize"] = True
                img.save(output_path, format="PNG", **save_kwargs)
            elif output_format == "webp":
                save_kwargs["quality"] = request.jpeg_quality
                img.save(output_path, format="WEBP", **save_kwargs)
            else:
                img.save(output_path)
    
    def _write_manifest(
        self, 
        export_path: Path, 
        dataset_files: List[DatasetFile],
        caption_set: CaptionSet,
        request: ExportRequest
    ):
        """Write a manifest file to the export directory."""
        manifest = self._generate_manifest(dataset_files, caption_set, request)
        manifest_path = export_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    def _generate_manifest(
        self,
        dataset_files: List[DatasetFile],
        caption_set: CaptionSet,
        request: ExportRequest
    ) -> dict:
        """Generate manifest data."""
        files_info = []
        for idx, df in enumerate(dataset_files):
            file_num = request.numbering_start + idx
            num_str = str(file_num).zfill(request.numbering_padding)
            
            files_info.append({
                "index": idx,
                "numbered_name": num_str,
                "original_filename": df.file.filename,
                "original_path": df.file.relative_path,
                "quality_score": df.quality_score
            })
        
        return {
            "export_date": datetime.utcnow().isoformat(),
            "caption_set": caption_set.name,
            "caption_style": caption_set.style,
            "total_files": len(files_info),
            "export_settings": {
                "image_format": request.image_format,
                "target_resolution": request.target_resolution,
                "min_quality_score": request.min_quality_score
            },
            "files": files_info
        }
    
    def get_export(self, export_id: str) -> Optional[ExportHistory]:
        """Get an export by ID."""
        return self.db.query(ExportHistory).filter(ExportHistory.id == export_id).first()
    
    def list_exports(self, status_filter: Optional[str] = None) -> List[ExportHistory]:
        """List exports."""
        query = self.db.query(ExportHistory)
        if status_filter:
            query = query.filter(ExportHistory.status == status_filter)
        return query.order_by(ExportHistory.created_date.desc()).all()
    
    def get_history(
        self, 
        dataset_id: Optional[str] = None, 
        limit: int = 20
    ) -> List[ExportHistory]:
        """Get export history."""
        query = self.db.query(ExportHistory)
        if dataset_id:
            query = query.filter(ExportHistory.dataset_id == dataset_id)
        return query.order_by(ExportHistory.created_date.desc()).limit(limit).all()
    
    def get_export_zip_path(self, export_id: str) -> Optional[Path]:
        """Get the path to an export's ZIP file."""
        export = self.get_export(export_id)
        if not export or export.export_type != "zip":
            return None
        
        path = Path(export.export_path)
        return path if path.exists() else None
