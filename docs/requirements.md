## Track B: Group Orders
Friends add items to one shared order, and the host checks out for everyone.
- A host creates a group order for one restaurant and receives a share code.
- Participants join with the code and add or remove their own items until the host locks the order. 
At most 10 participants; the order expires after 2 hours of inactivity.
- The summary shows each participant’s subtotal, and the delivery fee is split evenly with correct 
rounding (the parts must add up to the whole).
- When the host checks out, the group order becomes a normal MiniDash order.

### User Stories:
As the host, I want to create group orders for a restaurant so that I can invite my other friends to all order food together.

#### Criteria
1) When the host creates a group order for a valid restaurant, the system shall create the group order and return a unique share code for all members.
2) If the restaurant doesn't exist, the system will reject the order request with a 404 error.