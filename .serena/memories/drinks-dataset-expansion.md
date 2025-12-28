# Drinks Dataset Expansion

## Summary
Expanded the cocktail-cache drinks dataset from 74 to 142 drinks (91.9% increase).

## Final Counts
- **Cocktails**: 103 (was 50)
- **Mocktails**: 39 (was 24)
- **Total Drinks**: 142
- **Valid Ingredients**: 180

## Categories Added

### Classic Cocktails
Aviation, Last Word, Paper Plane, Penicillin, Corpse Reviver #2, French 75, Bee's Knees, Blood & Sand, Rob Roy, Rusty Nail, Godfather, Sidecar, Between the Sheets, Brandy Alexander, Singapore Sling, Caipirinha, Pisco Sour, Bramble, Amaretto Sour, The Journalist

### Tiki Cocktails
Zombie, Painkiller, Navy Grog, Hurricane, Planter's Punch, Jungle Bird, Fog Cutter, Scorpion, Three Dots and a Dash, Jet Pilot, Queen's Park Swizzle, Saturn, Chartreuse Swizzle, Suffering Bastard, Port au Prince

### Modern Classics
Naked and Famous, Division Bell, Oaxaca Old Fashioned, Tommy's Margarita, Final Ward, Gold Rush, Gimlet, White Lady, South Side, Clover Club, Trinidad Sour, New York Sour, Industry Sour, Midnight Margarita, Enzoni

### Low-ABV Aperitivo
Americano, Sbagliato, Aperol Spritz, Hugo Spritz, Bamboo, Adonis, Sherry Cobbler, Contessa, Chrysanthemum, Milano-Torino

### Highballs
Gin & Tonic, Whiskey Highball, Paloma, El Diablo, Dark 'n' Stormy, Horse's Neck, Presbyterian, Gin Rickey, Vodka Soda, Cuba Libre

### Regional Specialties
Vieux Carré, Sazerac, Toronto, Monte Carlo, Carajillo, Espresso Martini, Irish Coffee, Hot Toddy, Batida de Coco, Japanese Cocktail

### New Mocktails
Seedlip Garden & Tonic, Roy Rogers, Cinderella, Safe Sex on the Beach, Italian Sunrise, Ginger Rogers, Pomegranate Sparkler, Blueberry Lavender Lemonade, Spiced Apple Cider, Hibiscus Cooler, Matcha Highball, Coconut Lime Refresher, Elderflower Collins, Espresso Tonic, Raspberry Basil Smash

## New Ingredients Added

### Spirits
- islay-scotch, japanese-whisky, old-tom-gin, navy-strength-gin, demerara-rum, rhum-agricole, calvados

### Modifiers
- blanc-vermouth, lillet-blanc, cocchi-americano, cherry-heering, amaro-nonino, amaro-averna, amaro-montenegro, licor-43, dry-sherry, oloroso-sherry, port, st-elizabeth-allspice

### Syrups & Bitters
- mole-bitters, hibiscus-syrup, peach-syrup, blueberry-syrup, lime-cordial, don-mix

### Fresh Ingredients
- blueberry, raspberry, blackberry, peach, dill, serrano, habanero, hibiscus, matcha

### Mixers
- grapefruit-soda, condensed-milk, iced-tea, peach-nectar

## Schema
Each drink follows this structure:
```json
{
  "id": "kebab-case-id",
  "name": "Display Name",
  "tagline": "Short catchy description",
  "ingredients": [{"amount": "2", "unit": "oz", "item": "ingredient-id"}],
  "method": [{"action": "Shake", "detail": "description"}],
  "glassware": "rocks|coupe|collins|highball|etc",
  "garnish": "garnish description",
  "flavor_profile": {"sweet": 0-100, "sour": 0-100, "bitter": 0-100, "spirit": 0-100},
  "tags": ["tag1", "tag2"],
  "difficulty": "easy|medium|advanced",
  "timing_minutes": number,
  "is_mocktail": boolean
}
```

## Files Modified
- `data/cocktails.json` - 103 cocktails
- `data/mocktails.json` - 39 mocktails
- `data/ingredients.json` - 180 valid ingredients
