# Look guide: Bloodborne path tracing

The standing art rule for the RT renderer. Every lighting, fog, GI or exposure change is judged against it.
Numbers are tagged: **[stock]** = measured from the stock game (F9), **[src]** = from the sources below,
**[start]** = a starting value set by judgement, to be tuned against stock screenshots.

## 1. The look in one paragraph

Stock Bloodborne at night, lit the way a film like Nosferatu 2024 lights it: one hard, near-neutral moon
coming from a real direction; deep but readable shadows; pale things (petals, stone, mist, faces) as the
brightest areas of the frame; colour that drains away as light falls, so the darks are close to grey;
warmth only where a flame or lamp actually sits; and red that stays red where light reaches it. Fog
reads as moonlit white mist that pushes distance back, not as a coloured filter. Compared with stock,
the picture has more contrast and more direction (shadows that belong to a source, rims on backlit
shapes, shafts in the mist). It keeps stock's palette, grading, fog colour and overall brightness. It is
the same game, lit by a real moon.

## 2. Rules

1. **Moonlit pale surfaces land at 115-135 luma.** The top 10% of a moonlit white subject (lily petals,
   white stone, pale cloth) sits at 115-135. It is never below 110 and never more than about 8 above
   stock in the same view. [stock: 122-132. Ours was 95 before the highlight fix and is 119 now.]
   [src: day-for-night practice pulls highlights down below day level but keeps the brightest object
   clearly bright (Kroll, Mixing Light). Grimshaw keeps the brightest passage small and pale, often wet
   ground. Fuseli lights a white gown against a dark room.]
2. **Shadow floor 14-23 luma, never crushed.** The darkest 20% of geometry pixels sits at 14-23.
   Below 5 luma, no more than 0.5% of non-sky pixels. Texture must still be visible in the p5 band.
   [stock: p20 = 23. Ours is 16 now, which is inside the band.] [src: Blaschke keeps night readable
   rather than black; day-for-night keeps shadow detail instead of clipping (CineD, Kroll).]
3. **More contrast than stock, within limits.** The ratio of p90 to p20 luma is 5.5-8. [stock:
   127/23 = 5.5. Ours now: 119/16 = 7.4.] Ours goes darker in the shadows, not brighter in the lights.
   This is where "more dramatic" lives. [src: Ballhaus hard light; Laustsen single source with dark
   shadows; Asher lit colour like black and white.]
4. **Moonlight is neutral to slightly cool.** In the top 10% of moonlit pale surfaces, Lab b is -4 to
   +2 and Lab a is -3 to +2. Never cream, olive or yellow. [stock: near neutral. Ours is b +7, a -5,
   which breaks the rule. This is the "petals too greyish" report: a dirty olive cast reads as grey.]
   [src: measured moonlight is about 4100 K, slightly warmer than sun, yet seen as bluish because of
   the Purkinje shift (Wikipedia Moonlight; Gurney/Artist's Road). Blaschke drops most colour from
   moonlight. The two effects cancel to near neutral with a slight cool lean.]
5. **Saturation falls with luminance.** Mean Lab chroma C* of the darkest 20% is at most half that of
   the 40-80% band. Near-black pixels (luma < 20) have C* < 6. Lit midtones keep stock chroma.
   [src: Kirk & O'Brien 2011, Thompson/Shirley/Ferwerda 2002 (night = low contrast, low brightness,
   desaturated, blue-shifted), Patry 2021 Purkinje shift. [start] numbers.]
6. **Only fire and lamps are warm.** Pixels with b > +10 and luma > 40 appear only within the reach of
   a lamp, flame, torch or game glow. Moon-lit and sky-lit areas never turn warm through GI bounce or
   transmission. Where moonlight and lamplight meet, each keeps its colour; there is no muddy blend
   zone wider than the lamp's falloff. [src: Blaschke separates candle from moon because mixing
   muddies colour; Grimshaw places warm points in a cool, foggy field; Pan's Labyrinth sets warm
   against cold blue-green; Dark Souls bonfires; Lies of P gas-lamp colour temperatures.] Lamp hue is
   the game's own, pushed to the flame hue (`BB_RT_LAMP_HUE` 1, 0.61, 0.27).
7. **Red stays red where it is lit.** Blood, red cloth and red glass keep stock chroma (C* within 15%
   of stock) wherever their luma is above about 40. They may go dark in shadow like everything else.
   We never add red. [src: Bram Stoker's Dracula red over near black-and-white; Sleepy Hollow leaches
   colour except blood red; Crimson Peak's "very specific red in a very specific place"; Hammer's
   blood; Bloodborne's own greys and browns with crimson accents.]
8. **Motivated light only.** Every lit pixel traces to the moon, the sky, a lamp or flame, a game glow
   or a real bounce of those. No camera fill, no flat ambient, no lift added to make a dark spot match
   stock. [src: Blaschke "refused to fake" moonlight; Ballhaus: in Dracula's time every source was
   fire, oil or torch. Existing project rule.] Backlit places may stay darker than stock (see the lily
   field under the big tree).
9. **Hard moon shadows.** The moon is a small, distant source: sharp shadows with short penumbrae.
   Half-angle 0.25-0.5 degrees. [src: the real moon is about 0.26 degrees in half-angle; Blaschke uses a
   strong source far away for wide, hard-edged shadows.] Soft, blurry moon shadows are a defect.
10. **Fog is pale mist, stock colour.** Traced fog takes the stock fog colour and only adds light that
    the moon and lamps put into it. Distant geometry lifts toward the fog: the far-field luma is within
    +/-10 of stock. Moon shafts are visible but quiet: a shaft is 5-15 luma above the mist beside it.
    Fog never tints the scene. [src: Nosferatu 2024 white mist; Friedrich's mist and moonlit sky;
    Grimshaw's fog. [stock] for colour and far luma, [start] for the shaft range.]
11. **Silhouettes and rims when facing the moon.** A subject between camera and moon reads as a dark
    shape: interior luma at most half the bright mist or sky behind it, with thin bright edges from
    transmission (petals, hair, cloth) and grazing specular. No fill on the shadow side. [src:
    Friedrich's figures seen from behind against the moonlit sky; backlit day-for-night subjects
    (Beverly Boy); The Lighthouse's hard single sources.]
12. **Highlights roll off, small and few.** Above 250 luma, under 0.5% of the frame, except the moon
    disc, flames and lamp glass. Wet stone and puddles may carry the brightest geometry, in small
    patches. [src: Grimshaw's brightest passages on wet ground; day-for-night lowers the highlights.]
13. **Overall brightness follows stock.** The log-average luminance of lit geometry matches stock's
    -5.2 to -5.6 log2. Rules 1-3 then shape the spread around it. [stock: measured at the Hemwick gate
    and in the field.]
14. **Stock palette and grading stay.** We do not change albedo, the game's colour grading, its
    tonemap, sky or fog colour. Any shift in hue we introduce is a lighting effect (rules 4-6) and
    is bounded by those rules.

## 3. Mapping to knobs and code

| Rule | Knob(s) or change |
|---|---|
| 1 Pale surfaces 115-135 | `BB_RT_EXPOSURE_WHITE` (6 now; higher keeps more boost on highlights), `BB_RT_EXPOSURE_MAX` (1.5 EV), `BB_RT_THIN_TRANSMIT` (0.4; front-lit petals gain light through the back). Do not raise above stock + 8. |
| 2 Shadow floor | `BB_RT_GI_STRENGTH` (real bounce lifts shadows), `BB_RT_GI_FILL_SKY` (sky light on GI misses). If p20 drops below 14: more real sky/GI, never a flat ambient. |
| 3 Contrast ratio | Result of rules 1 and 2. `BB_RT_EXPOSURE_KEY` (-5.5) moves both ends; the white roll-off moves the top only. |
| 4 Neutral moon | **Needs a fix.** First find the source of the b +7 / a -5 cast: measure the top-10% Lab with `BB_RT_GI_STRENGTH=0`, then `BB_RT_THIN_TRANSMIT=0`, then `BB_RT_GI_DEBUG=3` (albedo as used). Likely causes: (a) transmission multiplies the light by the petal albedo and the reflection multiplies it again (albedo squared doubles the cream tint); fix: tint the transmitted term by albedo once, or by its luminance; (b) GI bounce from green grass dominates a backlit petal; fix: nothing artificial, but check the bounce albedo is not double-applied; (c) the game's moon/world light colour is warm; fix: if stock's own direct term is warm too, leave it, since stock's neutral look then comes from its ambient and rule 5's shift will balance it. |
| 5 Desaturate darks | **New code: a night shift** in `rt_exposure.comp` (it already runs on HDR scene colour before the game's bloom and tonemap, geometry only). Per pixel, from scene luminance L: weight w = 0 above a mid level, rising to a max (start 0.5) at the shadow floor. Mix colour toward its own luminance by w (desaturation), plus a small cool shift (start: at most b -3 at the floor, 0 at mid grey). Skip pixels whose light is mostly lamp (the lamp term from `rt_direct` or a warm-hue test) so firelight stays warm. Knobs: `BB_RT_NIGHT_SHIFT` strength, `BB_RT_NIGHT_MID`. Model reference: Patry's Purkinje delta (LMSR, gain `rsqrt(1 + LMS)`, add the rod term in opponent space) if a physical version is wanted; the simple mix is enough to start. |
| 6 Only fire warm | `BB_RT_LAMP_HUE`, `BB_RT_LAMP_WARM`, `BB_RT_LAMP_RANGE` (keep the falloff short), `BB_RT_FX_FOG_LIGHTS` (lamp glow in fog stays local). The night shift must exclude lamp-lit pixels. |
| 7 Red stays red | No knob. The night shift is luminance-weighted, so lit reds keep chroma. Check after any grading-like change. |
| 8 Motivated light | `BB_RT_FILL_ENCLOSED` (0.1 now; any fill must stay a real sky/GI stand-in, never a camera light). No new ambient terms. |
| 9 Hard shadows | `BB_RT_MOON_ANGLE` (tenths of a degree, 5 now). Range 3-5; 3 matches the real moon. |
| 10 Fog | `BB_RT_FX_FOG` on, `BB_RT_FX_FOG_STRENGTH` for far-field luma vs stock, `BB_RT_FX_FOG_SHAFT` for the shaft range, `BB_RT_FX_FOG_G` (0 now; a small forward lobe, start 0.3, makes shafts show toward the moon and fade away from it), `BB_RT_FX_FOG_SKY`. Fog colour stays the game's. |
| 11 Silhouettes | `BB_RT_THIN_TRANSMIT` (rims on petals), reflection strength `BB_RT_REFLECT_STRENGTH` (grazing specular). Exposure must not lift a backlit subject over its background: keep `BB_RT_EXPOSURE_MAX` at 1.5 or lower. |
| 12 Highlights | `BB_RT_EXPOSURE_WHITE` roll-off; the game's tonemap does the rest. |
| 13 Overall level | `BB_RT_EXPOSURE_KEY`, `BB_RT_EXPOSURE_RATE`. |
| 14 Stock grading | Nothing after the game's post chain. All our changes stay before bloom and tonemap. |

## 4. How to check

Use the same view, time and boot for each pair: ours, then F9 stock. Half-res screenshots, the same
luma formula as the existing measurements, sky masked out.

- **Percentiles of luma** over the region (petals or whole geometry): p5, p20, p50, p90, p99, % < 5,
  % > 250. Checks rules 1, 2, 3, 12, 13.
- **Lab of the top 10%** (by luma) of the pale subject: mean a and b. Checks rule 4. Also run it on a
  lamp-lit patch (expect b > +10) to check rule 6.
- **Chroma by luma band**: mean C* for the bottom 20% and the 40-80% band; C* of pixels with luma < 20.
  Checks rule 5. Run the same on stock to see what its grading already does.
- **Red patch**: C* of a lit blood or red cloth patch, ours vs stock. Checks rule 7.
- **Far field**: mean luma of the top third of geometry at more than 50 m, ours vs stock. Shaft vs
  neighbour luma on a vertical line through a shaft. Checks rule 10.
- **Backlit test**: face the moon in the lily field; subject interior luma / background luma <= 0.5.
  Checks rule 11.
- **Light source check**: `BB_RT_DIRECT_DEBUG=11` (with `BB_RT_RESTIR=0`) and `BB_RT_GI_DEBUG=1`; every
  bright area must come from a direct or GI term with a source. Checks rule 8.
- **Eye check**: ours and stock side by side. Same game, same palette, darker and harder? If it looks
  like a different art style, it fails, whatever the numbers say.

Reference views: Hemwick spawn gate, Hemwick lily field (toward and away from the moon), one lamp-lit
street in Yharnam, one interior with a fire.

## 5. What not to do

- **Crushed blacks.** "Darker" means a lower p20, not pixels at 0. Lost texture in the shadows is a
  failure, however moody it looks.
- **A blue wash.** No global cool tint, LUT or white-balance shift. Cool belongs only to the moonlit
  darks (rule 5), and the shift is small. A blue-green cast across lamps, faces and blood breaks rules
  6, 7 and 14.
- **A warm or olive moon.** The current petal cast. Bounce and transmission must not turn moonlight
  cream.
- **Fake fill.** No camera light, no flat ambient, no exposure push that lifts a backlit subject to
  front-lit brightness. If a place is too dark, find the missing real light (sky, GI, transmission).
- **Matching stock by brightening everything.** Stock is the reference for level and palette, not for
  where light comes from. A darker backlit field is correct.
- **Changing the stock palette.** No new hues, no saturation boost, no "Crimson Peak" red push, no
  grading after the game's post chain.
- **Fog as a filter.** Fog adds scattered light; it does not recolour the scene or flatten the
  contrast of the near field.
- **Soft, sourceless shadows.** A wide moon angle or heavy GI that removes the moon's shadow edges
  kills the drama.
- **Large blown highlights.** Big white patches on stone or petals look like a bug, not moonlight.
- **Purkinje by the book.** A full scotopic model at real moonlight levels would grey out the whole
  frame. The night shift is a light touch on the darks, capped by rules 4 and 5.

Gaps: no primary source was found for Van Helsing, Blasphemous, Beksinski or Lovecraftian illustration;
they inform the mood only, not any number here.

## 6. Sources

Films and cinematographers
- https://britishcinematographer.co.uk/jarin-blaschke-nosferatu/
- https://www.focusfeatures.com/article/nosferatu_interview_jarin-blaschke
- https://cined.com/behind-the-masterful-cinematography-of-nosferatu-dark-and-mesmerizing
- https://theasc.com/video/clubhouse-conversations-nosferatu/
- https://www.indepthcine.com/videos/jarin-blaschke
- https://theasc.com/articles/conjuring-a-coven-for-the-witch
- https://theasc.com/articles/stormy-isle-the-lighthouse
- https://www.kodak.com/en/motion/blog-post/robert-eggers-the-lighthouse
- https://theasc.com/articles/bram-stokers-dracula-a-happening-vampire
- https://cinephiliabeyond.org/dracula/
- https://www.pushing-pixels.org/?p=13349 (Laustsen, Crimson Peak)
- https://www.btlnews.com/?p=107597
- https://theasc.com/articles/flashback-sleepy-hollow
- https://www.salon.com/ent/movies/review/1999/11/19/sleepy/
- https://nxtbook.com/nxtbooks/ac/ac0107/index.php?startid=40 (Pan's Labyrinth, AC Jan 2007)
- https://banderasnews.com/0711/ent-panslabyrinth.htm
- https://www.horrifiedmagazine.co.uk/film/the-uniqueness-of-the-hammer-camera/
- https://en.wikipedia.org/wiki/Jack_Asher
- https://thebioscope.net/2008/07/05/colourful-stories-no-12-tinting-and-toning/
- https://brentonfilm.com/?p=10807 (Nosferatu 1922 tinting)
- https://www.pushing-pixels.org/2014/11/26/cinematography-of-penny-dreadful-interview-with-owen-mcpolin.html

Grading practice
- https://mixinglight.com/color-grading-tutorials/day-for-night
- https://noamkroll.com/color-grading-tutorial-creating-a-day-for-night-look/
- https://definitionmagazine.com/features/technique-day-for-night/
- https://beverlyboy.com/filmmaking/how-to-turn-a-day-shot-into-night/

Perception and rendering
- https://www2.eecs.berkeley.edu/Pubs/TechRpts/2011/EECS-2011-91.html (Kirk & O'Brien)
- https://history.siggraph.org/?p=114629
- https://advances.realtimerendering.com/s2021/jpatry_advances2021/index.html (Ghost of Tsushima, Purkinje shift)
- https://users.cs.utah.edu/docs/techreports/2000/pdf/UUCS-00-016.pdf (Thompson, Shirley, Ferwerda)
- https://en.wikipedia.org/wiki/Moonlight
- https://www.theartistsroad.net/p/the-blue-shift
- https://www.premiumbeat.com/blog/why-color-grade-moonlight-blue/

Paintings
- https://en.wikipedia.org/wiki/John_Atkinson_Grimshaw
- https://linesandcolors.com/?p=5127
- https://en.wikipedia.org/wiki/Two_Men_Contemplating_the_Moon
- https://smarthistory.org/?p=1346 (Fuseli, The Nightmare)
- https://www.thecollector.com/henry-fuseli-the-nightmare
- https://ipfs.ssi.eecc.de/ipns/en.wikipedia-on-ipfs.org/wiki/Black_Paintings
- https://www.naturalpigments.com/artist-materials/goya-color-palette-painting

Games
- https://gamerant.com/fromsoftware-good-consistent-art-direction-elden-ring-bloodborne/
- https://www.digitallydownloaded.net/2015/03/review-bloodborne-sony-playstation-4.html
- https://www.unrealengine.com/developer-interviews/lies-of-p-takes-inspiration-from-pinocchio-french-history-and-marries-them-with-soulslike-combat
- https://jbhifi.com.au/blogs/games/puppet-master-lies-of-p-q-a
- https://wiki.riteme.site/wiki/Bonfire_(Dark_Souls)
- https://gamedeveloper.com/art/romanticism-and-the-art-of-dark-souls-iii
