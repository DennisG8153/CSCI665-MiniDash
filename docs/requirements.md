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
As the other members of the group, I want to be able to join an existing group order using a code, so I can add my order to the shared order. (I.E, Stacy has a group but Sharon wants to join. Stacy can give Sharon a code to join.)
As the host, I want to be able to control when my party can add more items and be able to "lock" the party in case I don't want to order more.

#### Criteria
1) When the host creates a group order for a valid restaurant, the system shall create the group order and return a unique share code for the host to share with their members.
2) If the restaurant doesn't exist, the system will reject the order request with a 404 error.
3) Whenever a member enters a valid code for an active and unplaced order, the system will add that person to the group, so long as the group is unlocked still.
4) If the host checks out, the group order becomes a normal MiniDash order.
5) If a person enters a code that doesn't exist, is wrong, has expired, or is out of date because the order has been accepted, the system shall reject the person with an error.
6) If a group order already has ten members, the system will reject any new requests to join automatically.
7) If a group order has two or more hours of inactivity, the order will expire and the host will have to start a new group order. 
8) If a group order is locked by the host, the system will reject the request without changing who already exists in the group.
9) The summary of the total order will be split based on what each member of the group ordered.
10) The delivery fees of the order will be split evenly among all participants with correct rounding.
11) When a member adds a valid menu item to an active and unlocked group order, the system shall add that item to the group order. 
13) When a member removes a valid menu item to an active and unlocked group order, the system will remove the item from the group order.
14) Only the host should be able to lock the order and check out.

### Out of Scope:
1) Both TRACK A and TRACK C are not requirements for this project.
2) The track will not calculate any taxes as taxation is dependant on the state.
3) The track will also not dynamically calculate delivery fees as they require geo-locations and for the restaurants to have addresses saved. These restaurants are mostly fake (even though the names were created mostly by me and actual restaurants that do exist like Nozu and Taco Bell.)
4) For the simplicity of this project, we are assuming that the delivery fee for all orders is $15.95 USD.