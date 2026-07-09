/** Static layout for the site floor-plan heatmap.

Each zone is positioned on a 2D construction-site map using a normalized
coordinate space (see FLOOR_PLAN_VIEWBOX). The positions are UI-only
configuration — they are not derived from the backend, which only
supplies per-zone violation counts. Adjust these coordinates to match a
real site layout without touching component code.
*/

export interface FloorZoneLayout {
  /** Zone id (1-6), matches backend zone config. */
  zone_id: number;
  /** Top-left x in viewBox units. */
  x: number;
  /** Top-left y in viewBox units. */
  y: number;
  /** Width in viewBox units. */
  w: number;
  /** Height in viewBox units. */
  h: number;
}

/** SVG viewBox dimensions for the floor plan. */
export const FLOOR_PLAN_VIEWBOX = { width: 1000, height: 470 };

/**
 * Zone rectangles laid out as a 3-column x 2-row site map.
 * Order here is purely spatial (top-left -> bottom-right).
 */
export const FLOOR_ZONE_LAYOUT: FloorZoneLayout[] = [
  { zone_id: 3, x: 40, y: 40, w: 280, h: 170 }, // Welding Zone (top-left)
  { zone_id: 4, x: 360, y: 40, w: 280, h: 170 }, // Concrete Zone (top-mid)
  { zone_id: 5, x: 680, y: 40, w: 280, h: 170 }, // Loading Zone (top-right)
  { zone_id: 2, x: 40, y: 250, w: 280, h: 170 }, // Scaffold Zone (mid-left)
  { zone_id: 6, x: 360, y: 250, w: 280, h: 170 }, // Material Yard (mid-mid)
  { zone_id: 1, x: 680, y: 250, w: 280, h: 170 }, // Entry Gate (mid-right)
];
