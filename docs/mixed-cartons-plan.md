# Shared cartons in Cost Calculator

## Agreed rules

- Only items from the same supplier may share cartons. Compare trimmed supplier names without case sensitivity. Ask for a supplier before grouping items with a blank supplier.
- Enter carton length, width, height and capacity when creating a group. These values belong to this packing group, independently of each item's usual carton settings.
- Grouping is explicit. Matching supplier, colour or dimensions must never group items automatically.
- The user confirms which compatible products physically fit the stated capacity. A common capacity of 10 means ten individual units across all products in the group.

## User flow

1. Select catalogue items and enter purchase quantities as usual. Their item numbers remain visible.
2. Choose **Group into cartons** and select the same-supplier lines and quantities to pack together. A line can contribute part of its purchase quantity.
3. Enter a group name, dimensions in centimetres and the number of units that fit in one carton. Show available quantities, assigned quantities and remaining quantities beside each line.
4. Show the resulting carton count, CBM and international shipping before applying the group.
5. Display a Cartons section below the item table, with each group's contents and **Edit** / **Ungroup** controls. Item rows show their group names so the packing is traceable.
6. Quantity changes recalculate packing. If a quantity falls below its assigned units, flag the affected group and require an adjustment before saving. Never silently assign the same units twice.

Search and sorting change the view only. Clearing search must preserve packing groups and all purchase quantities.

## Calculation

For each group:

- Units packed = sum of the quantities explicitly assigned to that group.
- Cartons = round units packed / capacity up to a whole number. An empty group contributes zero cartons and is removed.
- CBM per carton = length × width × height / 1,000,000.
- Group CBM = cartons × CBM per carton.
- Group international shipping = group CBM × the calculation's shipping rate.

Calculate each item's unassigned quantity using its normal units-per-carton and dimensions. Add those ungrouped cartons to the shared groups once. The overall carton and CBM totals come from physical packing groups and ungrouped cartons, rather than summing a full shared carton once for each item.

Keep purchase prices, quantity price tiers, local shipping and fees under their existing rules. Allocate shared international shipping to item lines by their assigned unit quantities, using full precision internally. A shared carton's physical count belongs to the group; do not label each member line as an additional whole carton. Display currency rounding must not create extra shipping charges.

## Worked example

Assume one supplier and a carton measuring 60 × 40 × 40 cm with capacity 10. Each carton is 0.096 CBM.

| Packing | Physical cartons | Total CBM |
| --- | ---: | ---: |
| 4 units of A + 6 of B, grouped | 1 | 0.096 |
| 5 units of A + 6 of B, grouped | 2 | 0.192 |
| 1 unit each of ten different items, grouped | 1 | 0.096 |

Quantities not assigned to these groups retain separate carton calculations. For example, buying 14 units of A but assigning only 4 to a mixed group leaves 10 units of A to pack normally.

## Saving and historical lists

- Save group dimensions, capacity, quantities, calculated cartons and shipping allocations alongside the saved item snapshots. Include item numbers and the calculation's shipping rate.
- Store physical carton groups separately from item lines, with memberships linking their assigned units. Apply the same per-user ownership checks as existing saved-list data.
- Save the list, lines, carton groups and memberships in one transaction. A partially saved packing plan must never appear as a complete list.
- Existing saved lists retain their historical carton and shipping values. New packing data must not recalculate them on view.
- **Duplicate & recalculate** restores the packing groups and recalculates with current prices and the chosen shipping rate, flagging missing catalogue items or insufficient quantities.

## Validation before release

- Same-supplier grouping succeeds; different or missing suppliers are rejected.
- Quantities of 1, 10 and 11 at capacity 10 produce 1, 1 and 2 cartons.
- Partial allocations and multiple groups never exceed the purchased quantity.
- Different dimensions and capacities use the group's entered values.
- Grouping and ungrouping preserve all purchased units and reconcile shipping allocations to physical carton totals.
- Search, Clear buttons, sort changes and selected-item deletion cannot silently alter packing.
- Saving/reopening preserves group data; changing the catalogue does not change historical lists.
- Saved-list duplication, CSV and print clearly distinguish physical cartons from item membership.

This document is the implementation plan. The current release adds item numbers, search Clear buttons and bulk deletion; shared-carton calculations will be implemented in the packing update.
