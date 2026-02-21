# Naming and Exports

## Naming Rule

Output naming is deterministic and versioned:

`<input_stem>_<preset_name>_vNNN.<ext>`

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
