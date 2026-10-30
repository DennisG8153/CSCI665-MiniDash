## Track B: Group Orders
Friends add items to one shared order, and the host checks out for everyone.
- A host creates a group order for one restaurant and receives a share code.
- Participants join with the code and add or remove their own items until the host locks the order. 
At most 10 participants; the order expires after 2 hours of inactivity.
- The summary shows each participant’s subtotal, and the delivery fee is split evenly with correct 
rounding (the parts must add up to the whole).
- When the host checks out, the group order becomes a normal MiniDash order.

### User Stories:
1) As the host, I want to create group orders for a restaurant so that I can invite my other friends to all order food together.
2) As the other members of the group, I want to be able to join an existing group order using a code, so I can add my order to the shared order. (I.E, Stacy has a group but Sharon wants to join. Stacy can give Sharon a code to join.)
3) As the host, I want to be able to control when my party can add more items and be able to "lock" the party in case I don't want to order more.

#### Criteria
1) WHEN the HOST CREATES a group order for a valid restaurant, THE SYSTEM SHALL create the group order and return a unique share code for the host to share with their members.
2) IF the restaurant DOESN'T EXIST, THE SYSTEM SHALL reject the order request with a 404 error.
3) WHENEVER A MEMBER enters a valid code for an active and unplaced order, THE SYSTEM SHALL add that person to the group, so long as the group is unlocked still.
4) WHEN the host checks out a locked group order, THE SYSTEM SHALL create one normal MiniDash order containing all the member's items and prevent the group order from being checked out again.
5) IF A PERSON enters a code that doesn't exist, is wrong, has expired, or is out of date because the order has been accepted, THE SYSTEM SHALL reject the person with an error.
6) IF A GROUP order already has ten members, THE SYSTEM SHALL reject any new requests to join automatically.
7) IF A GROUP order has two or more hours of inactivity, THE SYSTEM SHALL make the order expire and the host will have to start a new group order. 
8) IF a successful group activity happens by the members, THE SYSTEM SHALL reset the inactivity timer.
9) WHEN the host locks an active group order, THE SYSTEM SHALL prevent members from joining, adding items, or removing items.
10) WHEN an order is placed, THE SYSTEM SHALL display each member's subtotal based on the items they selected.
11) WHEN an order is placed, THE SYSTEM SHALL divide the delivery fee among all member's using integer cents evenly with correct rounding.
12) WHEN a member adds a valid menu item to an active and unlocked group order, THE SYSTEM SHALL add that item to the group order. 
13) WHEN a member removes a valid menu item to an active and unlocked group order, THE SYSTEM SHALL remove the item from the group order.
14) WHEN a member attempts to modify another member's items, THE SYSTEM SHALL reject the request without changing the group order.
15) WHEN a member other than the host attempts to lock a group order, THE SYSTEM SHALL reject the request without changing the group's status.
16) WHEN any member attempts to add or remove items after the group order is locked, THE SYSTEM SHALL reject the request without modifying the order.

#### Out of Scope:
1) Both TRACK A and TRACK C are not requirements for this project.
2) The track will not calculate any taxes as taxation is dependant on the state.
3) The track will also not dynamically calculate delivery fees as they require geo-locations and for the restaurants to have addresses saved. These restaurants are mostly fake (even though the names were created mostly by me and actual restaurants that do exist like Nozu and Taco Bell.)
4) For the simplicity of this project, we are assuming that the delivery fee for all orders is $15.95 USD.
5) For the simplicity of this project, we are assuming that the members of the group and the host all agree to order together and that the host cannot remove what other people order.