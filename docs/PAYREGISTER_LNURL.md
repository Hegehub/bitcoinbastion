# PAYREGISTER_LNURL.md

## PayRegister comments

PayRegister may enable LNURL-pay comments for order references, receipt notes, cashier-visible notes, merchant invoice references, or support references. Store and terminal policy set the effective maximum; cashiers cannot increase it from the callback. Comments cannot change invoice amount, merchant destination, terminal identity, cashier authentication, refund approval, or entitlement rules.

Receipt views must escape comments before display. Receipt packets may include a comment hash and classification, not raw unredacted text unless a merchant policy explicitly enables encrypted short-retention storage.
