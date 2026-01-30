# Vision Model Prompting Guide

This document explains how CaptionFoundry constructs prompts when sending images to vision language models (VLMs) for automatic caption generation.

## Overview

CaptionFoundry uses a **two-part prompt architecture** that separates concerns:

1. **Creative Prompt** (User-Customizable)
   - Controls the style, tone, and content of the generated caption
   - Can be one of three predefined styles or completely custom
   - Can include trigger phrases and length constraints
   - This is what users edit when creating caption sets

2. **Output Directive** (System-Enforced)
   - Always appended to every prompt automatically
   - Ensures consistent JSON output format
   - Requests quality assessment metadata
   - **Users cannot modify this** - it's critical for parsing responses

This separation ensures that:
- Users can fully customize the creative instructions without breaking the system
- The application can reliably parse responses from any vision model
- Quality assessment is consistently included in all generated captions

---

## Prompt Construction Process

### Step 1: Build Creative Prompt

The system first builds the creative part based on the caption set style:

**For Predefined Styles** (`natural`, `detailed`, `tags`):
- Uses the built-in template for that style
- See templates in the next section

**For Custom Style**:
- Uses the exact custom prompt text provided by the user
- No modifications to the user's creative instructions

### Step 2: Add Optional Modifiers

**Trigger Phrase** (if specified):
- For tag-based styles: Instructs model to start with trigger phrase as first tag
- For sentence styles: Instructs model to begin caption with trigger phrase
- Example: `IMPORTANT: The caption MUST begin with "ohwx woman" followed by a description of the image.`

**Maximum Length** (if specified):
- Adds a character limit constraint
- Example: `Maximum length: 150 characters.`

### Step 3: Append System Output Directive

The system automatically appends the output directive that:
- Requests quality assessment scores
- Specifies the required JSON output format
- Ensures parseable responses

### Step 4: Send to Vision Model

The complete prompt (Creative + System Directive) is sent to the vision model along with the base64-encoded image.

---

## Predefined Style Templates

### Natural Style

**Purpose**: Concise, single-sentence descriptions suitable for most training scenarios.

**Creative Prompt**:
```
Describe this image in one clear, concise sentence suitable for AI image generation training.
Focus on: main subject, action/pose, setting/background.
Be objective and descriptive. Avoid subjective interpretations.
```

**Best For**:
- General-purpose training datasets
- Balanced descriptions that capture key elements
- Natural language captions for image generation models

**Example Output**:
```
A woman with long brown hair wearing a white dress stands in a sunlit garden with rose bushes in the background.
```

---

### Detailed Style

**Purpose**: Multi-sentence descriptions with rich environmental and compositional details.

**Creative Prompt**:
```
Provide a detailed 2-3 sentence description of this image suitable for AI training.
Include: subjects, actions, environment, mood, lighting, notable details, composition.
Be specific and objective.
```

**Best For**:
- High-quality training datasets requiring comprehensive descriptions
- Capturing subtle details, lighting, and atmosphere
- Professional photography or complex scenes

**Example Output**:
```
A young woman with shoulder-length auburn hair and green eyes gazes directly at the camera with a slight smile. She wears an elegant white lace dress with long sleeves, and soft natural light from a window illuminates her face from the left side. The background shows a blurred outdoor garden setting with warm bokeh from flowering plants.
```

---

### Tags Style

**Purpose**: Comma-separated keyword tags for booru-style or tag-based training.

**Creative Prompt**:
```
Generate 15-25 comma-separated lowercase tags describing this image. NOT a sentence - just tags separated by commas.
Include: subject, gender, pose/action, clothing details, hair color/style, eye color, background/setting, lighting, colors, mood.
```

**Best For**:
- Booru-style tagging systems
- Tag-based training datasets
- Datasets requiring structured metadata
- Easy filtering and searching by specific attributes

**Example Output**:
```
woman, solo, long brown hair, green eyes, white dress, lace dress, standing, looking at viewer, slight smile, garden, outdoor, roses, flowers, natural lighting, soft lighting, warm colors, spring, portrait
```

---

### Custom Style

**Purpose**: Complete control over prompt structure for specialized use cases.

**How It Works**:
1. User provides their own complete creative prompt text
2. System uses it verbatim (no predefined template)
3. Optional modifiers (trigger phrase, length) are still added if specified
4. System directive is still appended automatically

**Best For**:
- Specialized domains (medical, technical, artistic)
- Specific output formats or requirements
- Experimentation with prompt engineering
- Domain-specific terminology or focus areas

**Example Custom Prompt**:
```
Describe this fashion photograph in the style of a professional fashion magazine caption. 
Focus on: garment details, fabric textures, styling choices, color palette, and the overall aesthetic mood. 
Use fashion industry terminology where appropriate. Be sophisticated and concise.
```

**Example Output**:
```
The model showcases an ethereal ivory silk organza gown with hand-embroidered lace appliqués along the bodice. Romantic puff sleeves and a flowing A-line silhouette create a dreamy, whimsical aesthetic, perfectly complemented by the soft-focus garden backdrop and golden hour lighting.
```

---

## Complete Prompt Examples

Below are complete examples showing exactly what is sent to the vision model for each style.

### Example 1: Natural Style

**Caption Set Configuration**:
- Style: `natural`
- Trigger Phrase: None
- Max Length: None

**Complete Prompt Sent to Vision Model**:
```
Describe this image in one clear, concise sentence suitable for AI image generation training.
Focus on: main subject, action/pose, setting/background.
Be objective and descriptive. Avoid subjective interpretations.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "A woman with long brown hair wearing a white sundress stands in a sunlit garden surrounded by blooming roses.",
  "quality": {
    "sharpness": 0.85,
    "clarity": 0.90,
    "composition": 0.88,
    "exposure": 0.92,
    "overall": 0.89
  },
  "flags": ["good_lighting", "well_composed"]
}
```

---

### Example 2: Natural Style with Trigger Phrase

**Caption Set Configuration**:
- Style: `natural`
- Trigger Phrase: `ohwx woman`
- Max Length: None

**Complete Prompt Sent to Vision Model**:
```
Describe this image in one clear, concise sentence suitable for AI image generation training.
Focus on: main subject, action/pose, setting/background.
Be objective and descriptive. Avoid subjective interpretations.

IMPORTANT: The caption MUST begin with "ohwx woman" followed by a description of the image.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "ohwx woman with long brown hair wearing a white sundress stands in a sunlit garden surrounded by blooming roses.",
  "quality": {
    "sharpness": 0.85,
    "clarity": 0.90,
    "composition": 0.88,
    "exposure": 0.92,
    "overall": 0.89
  },
  "flags": []
}
```

---

### Example 3: Detailed Style with Max Length

**Caption Set Configuration**:
- Style: `detailed`
- Trigger Phrase: None
- Max Length: `200`

**Complete Prompt Sent to Vision Model**:
```
Provide a detailed 2-3 sentence description of this image suitable for AI training.
Include: subjects, actions, environment, mood, lighting, notable details, composition.
Be specific and objective.

Maximum length: 200 characters.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "A woman with brown hair in a white dress stands among roses. Soft sunlight creates warm tones and gentle shadows. The garden setting and natural pose convey a peaceful, romantic mood.",
  "quality": {
    "sharpness": 0.87,
    "clarity": 0.91,
    "composition": 0.85,
    "exposure": 0.90,
    "overall": 0.88
  },
  "flags": ["slight_motion_blur"]
}
```

---

### Example 4: Tags Style

**Caption Set Configuration**:
- Style: `tags`
- Trigger Phrase: None
- Max Length: None

**Complete Prompt Sent to Vision Model**:
```
Generate 15-25 comma-separated lowercase tags describing this image. NOT a sentence - just tags separated by commas.
Include: subject, gender, pose/action, clothing details, hair color/style, eye color, background/setting, lighting, colors, mood.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "woman, solo, long brown hair, green eyes, white dress, sundress, standing, looking at viewer, slight smile, garden, outdoor, roses, red flowers, natural lighting, soft lighting, warm colors, spring, portrait, depth of field",
  "quality": {
    "sharpness": 0.88,
    "clarity": 0.92,
    "composition": 0.90,
    "exposure": 0.91,
    "overall": 0.90
  },
  "flags": []
}
```

---

### Example 5: Tags Style with Trigger Phrase

**Caption Set Configuration**:
- Style: `tags`
- Trigger Phrase: `ohwx`
- Max Length: None

**Complete Prompt Sent to Vision Model**:
```
Generate 15-25 comma-separated lowercase tags describing this image. NOT a sentence - just tags separated by commas.
Include: subject, gender, pose/action, clothing details, hair color/style, eye color, background/setting, lighting, colors, mood.

IMPORTANT: The caption MUST start with "ohwx" as the first tag.
Example: "ohwx, woman, brown hair, white dress, studio, soft lighting"

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "ohwx, woman, solo, long brown hair, green eyes, white dress, sundress, standing, looking at viewer, garden, outdoor, roses, flowers, natural lighting, soft lighting, warm colors, spring, portrait",
  "quality": {
    "sharpness": 0.88,
    "clarity": 0.92,
    "composition": 0.90,
    "exposure": 0.91,
    "overall": 0.90
  },
  "flags": []
}
```

---

### Example 6: Custom Style

**Caption Set Configuration**:
- Style: `custom`
- Custom Prompt: `Analyze this image as if you are an expert art critic. Describe the composition, use of color, lighting techniques, and emotional impact. Focus on artistic elements rather than literal descriptions. Be concise but insightful.`
- Trigger Phrase: None
- Max Length: None

**Complete Prompt Sent to Vision Model**:
```
Analyze this image as if you are an expert art critic. Describe the composition, use of color, lighting techniques, and emotional impact. Focus on artistic elements rather than literal descriptions. Be concise but insightful.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "The image employs classical portraiture techniques with soft, diffused natural light creating a romantic atmosphere. The composition follows the rule of thirds, positioning the subject off-center against a deliberately blurred floral background that creates depth through selective focus. Warm color harmony between the ivory dress and golden garden tones evokes tranquility and timeless elegance.",
  "quality": {
    "sharpness": 0.86,
    "clarity": 0.89,
    "composition": 0.94,
    "exposure": 0.90,
    "overall": 0.90
  },
  "flags": ["professional_quality", "artistic_composition"]
}
```

---

### Example 7: Custom Style with All Modifiers

**Caption Set Configuration**:
- Style: `custom`
- Custom Prompt: `Write a technical description suitable for a medical imaging database. Include observable anatomical features, positioning, lighting conditions, and image quality notes.`
- Trigger Phrase: `medical scan`
- Max Length: `180`

**Complete Prompt Sent to Vision Model**:
```
Write a technical description suitable for a medical imaging database. Include observable anatomical features, positioning, lighting conditions, and image quality notes.

IMPORTANT: The caption MUST begin with "medical scan" followed by a description of the image.

Maximum length: 180 characters.

Also assess the image quality for training suitability.

Output format (JSON only, no other text):
{
  "caption": "Your caption here",
  "quality": {
    "sharpness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "composition": 0.0-1.0,
    "exposure": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "flags": ["list", "of", "any", "quality", "issues"]
}
```

**Example Model Response**:
```json
{
  "caption": "medical scan showing frontal view, subject centered, even illumination, no motion artifacts, adequate resolution for diagnostic review, standard positioning protocol followed",
  "quality": {
    "sharpness": 0.92,
    "clarity": 0.95,
    "composition": 0.88,
    "exposure": 0.93,
    "overall": 0.92
  },
  "flags": []
}
```

---

## Quality Assessment

Every caption generation includes automatic quality assessment with five metrics:

- **Sharpness** (0.0-1.0): Image focus and detail clarity
- **Clarity** (0.0-1.0): Overall visual clarity and noise levels
- **Composition** (0.0-1.0): Framing, subject placement, and visual balance
- **Exposure** (0.0-1.0): Brightness and dynamic range
- **Overall** (0.0-1.0): Weighted average quality score

**Quality Flags** may include:
- Positive: `good_lighting`, `well_composed`, `professional_quality`, `high_resolution`
- Negative: `blur`, `noise`, `overexposed`, `underexposed`, `poor_composition`, `low_resolution`

These metrics help you:
- Filter low-quality images from training datasets
- Identify images that need recapturing or editing
- Make informed decisions about dataset curation

---

## Best Practices

### Choosing a Style

- **Natural**: Default choice for most use cases. Produces balanced, readable captions.
- **Detailed**: When you need comprehensive scene descriptions or training high-fidelity models.
- **Tags**: For booru-style datasets, metadata tagging, or structured attribute extraction.
- **Custom**: When you have domain-specific requirements or want to experiment.

### Using Trigger Phrases

Trigger phrases (also called activation tokens) are useful for:
- Training LoRAs or embeddings for specific subjects
- Maintaining consistency across a training set
- Identifying specific concepts in generated images

**Tips**:
- Keep trigger phrases short (2-4 words)
- Use unique, memorable tokens: `ohwx woman`, `sks dog`, `bnk style`
- Be consistent across your entire dataset

### Setting Max Length

Character limits are useful when:
- Training models with fixed-length caption requirements
- Keeping descriptions concise for fast generation
- Matching specific dataset conventions

**Recommendations**:
- Natural style: 150-250 characters
- Detailed style: 300-500 characters
- Tags style: No limit (let model generate full tag list)
- Custom style: Depends on your requirements

### Custom Prompt Tips

When writing custom prompts:
1. **Be specific** about what you want described
2. **Specify format** (sentences, tags, technical terms, etc.)
3. **Include examples** if you want a particular style
4. **Set clear constraints** (length, vocabulary, focus areas)
5. **Remember**: The system directive is always added—don't worry about JSON format

**Good Custom Prompt Example**:
```
Describe this image in the style of a Victorian novel. 
Use elegant, formal language with rich descriptive adjectives. 
Focus on: clothing details, setting atmosphere, subject's demeanor. 
Keep to 2 sentences maximum.
```

**Poor Custom Prompt Example**:
```
Describe the image. Include what you see.
```
(Too vague, no clear direction or constraints)

---

## Technical Notes

### Response Parsing

CaptionFoundry handles various response formats:
- Standard JSON (preferred)
- JSON wrapped in markdown code blocks (```json ... ```)
- Plain text fallback if JSON parsing fails

The system automatically:
- Strips markdown formatting
- Removes common prefixes ("Caption:", "Description:", etc.)
- Extracts caption text even from malformed responses

### Error Handling

If the model doesn't follow the JSON format:
- System extracts the raw text as the caption
- Quality scores are set to `null`
- Generation succeeds (doesn't fail the entire job)

## Summary

CaptionFoundry's two-part prompt architecture gives you:

✅ **Full creative control** over caption style and content  
✅ **Consistent output format** that the system can reliably parse  
✅ **Quality assessment** built into every caption generation  
✅ **Flexibility** from simple presets to advanced custom prompts  
✅ **Safety** by preventing users from breaking JSON parsing  

Whether you're training a character LoRA, building a style dataset, or creating comprehensive image descriptions, CaptionFoundry's prompting system adapts to your needs while maintaining reliability.
