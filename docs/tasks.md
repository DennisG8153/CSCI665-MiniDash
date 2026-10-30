# MiniDash - Track B Implementation Tasks

## Implementation Plan
The group orders feature will be developed in smaller, testable slices. Each slice will be reviewed, tested, and committed separately.

### Slice 1: Group Order Database
- Add group_orders, group_members, and group_order_items tables.
- Define the foreign keys (FK) and their relationships.
- Define database constraints.
- Verify that the tables can be created successfully.
TEST: Verify that all three tables exist and invalid FK references are rejected.

### Slice 2: Group Creation
- Implement the API endpoints (POST) /group_orders.
- Generate unique share codes.
- Creates the host as the first member.
- Reject nonexistent restaurants.
TEST: Verify that creating a group with a valid restaurant succeeds and with an invalid restaurant fails.

### Slice 3: Joining Groups
- Implement the API endpoints (POST) /group_orders/{code}/join.
- Enforce 10 member limit.
- Reject invalid codes.
- Reject joining locked or expired groups.
TEST: Verify successful joining and rejection of an 11th member.

### Slice 4: Member Item Management
- Implement adding menu items.
- Implement removing menu items.
- Validate item ownership.
- Prevent changes to locked groups.
TEST: Verify that members can modify their items but cannot modify another member's items.

### Slice 5: Group Summary & Delivery Fees
- Calculate each member's subtotal.
- Apply the fixed $15.95 delivery fee.
- Split the fee using integer cents.
- Ensure allocated fees total up to exactly 1595.
TEST: Verify fee rounding for groups of different sizes and correct member subtotals.

### Slice 6: Locking and Expiration
- Implement HOST-ONLY locking.
- Track successful group activity.
- Expire groups after two hours of inactivity.
- Prevent changes after expiration.
TEST: Verify that only the host can lock the group, locked-group restrictions, and expiration at the two-hour boundary.

### Slice 7: Normal Order Checkout
- Complete the required normal-order API functionality if not already implemented.
- Implement POST /group_orders/{code}/checkout.
- Convert group items into ONE normal order.
- Prevent duplicate checkouts.
- Save checkout changes automatically.
- TEST: Verify one normal order is created with the correct items, total, and that repeated checkouts do not create duplicates.

### Slice 8: Final Verification and Documentation
- Run all automated tests.
- Run the linter and inspect code changes.
- Verify dependencies against their registries.
- Update README.md with setup instructions.
- Complete AI_Log.md and reflection.
- Prepare 5-min demo.
TEST: Verify that the application and tests work from a clean project set-up.