# MiniDash - Track B: Group Orders

## 1. Design Overview

The group orders features will extend the existing MiniDash REST API to allow multiple people to contribute items to one shared restaurant order. The host will create a group order and receives a unique share code. Other members join using that code. Members can add or remove their own menu items while the group order is open. The host can lock the group order to prevent further modifications and then complete checkout. After checkout is accepted, the group order is then considered one normal MiniDash order. 

The implementation will use Python, FastAPI, and SQLite while following the pre-existing layered architecture. 

## 2. Components Affected
- `src/main.py`: Register the group order API routes.
- `src/models.py`: Add data validation models.
- `src/repository/schema.py`: Add group order database tables.
- Normal order functionality: Support group order checkout.

## 3. New Components
The group orders feature will introduce three main components: 
1. Group Ordering Routes:
- Accept HTTP requests relating to group orders
- Validate incoming request data
- Return appropriate HTTP responses.

2. Group Order Service
- Enforce participant limits.
- Validate item ownership.
- Manage locking and expiration.
- Calculate subtotals and delivery fee splits.
- Coordinate checkout

3. Group Order Repository 
- Store group orders in SQLite
- Store members and their menu items
- Retrieve and update group-order records.

The existing restaurant repository will be reused to validate restaurants and menu items. The existing normal order functionality will also be reused during group checkout.


## 4. API Interfaces
The group orders feature will introduce new rest API endpoints using FastAPI.

### Group Creation:
POST /group-orders --> Creates a new group order for one restaurant.
Requests: 
- restaurant_id
- host_name
Response:
- group_order_id
- share_code
- status (Open/Closed) as a bool
- host identifier

### Joining a Group
POST /group-orders/{code}/join
This will allow other users to join an existing group using a valid share code.
Request:
- member_name
Response:
- member_id
- group_order_id
- status
Restrictions:
- A maximum of 10 members, including the host.
- Joining is prohibited after locking or expiration.
### Adding Items
POST /group-orders/{code}/items
Adds a menu item to a member's group order.
Request:
- member_id
- menu_item_id
- quantity
Restrictions:
- The group has to be OPEN.
- The item MUST exist and belong to the group's restaurant.
- Members can only modify THEIR OWN items.
### Removing Items
DELETE /group-orders/{code}/items/{item_id}
Removes an item from a member's group order.
Request:
- host authorized credential
- delivery_a