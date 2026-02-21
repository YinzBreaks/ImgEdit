# Naming and Exports

## Naming Rule

Output naming is deterministic and versioned:

`<input_stem>_<preset_name>_vNNN.<ext>`

When `export.include_relpath_slug=true`, output naming uses relative-path slugging to prevent stem collisions across subfolders:

`<relpath_slug>_<preset_name>_vNNN.<ext>`

Example:

- Input `in/subA/IMG_0001.png`
- Preset `instagram_4x5`
- Output `suba__img_0001_instagram_4x5_v001.png`

Slug rules:

- lowercase
- non-alphanumeric characters become `_`
- multiple separators collapse inside each segment
- relative path segments are joined with `__`

Examples:

- `product_a_instagram_4x5_v001.png`
- `product_a_instagram_4x5_v001.jpg`
- `product_a_ebay_square_v002.png`

## Channel Size Rules

- Instagram 4:5: `1080x1350`
- eBay square: `1600x1600`
- eBay gallery: `1600x1200`
- Print canvas matte 8.5x11 @300dpi: `2550x3300`

## Overwrite Policy

Never overwrite. If `v001` exists, next export becomes `v002`.

Dry-run computes the same next version numbers that a real run would choose at execution time.
