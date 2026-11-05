# RPA test scenarios

1. Search `OPP-000001`; expect exactly one opportunity.
2. Select the first open activity whose due date is in the past; create a follow-up and verify a new activity appears.
3. Download `Q-2023-000001`; verify the displayed total equals its line-item sum.
4. Open the first record in the corrupted extract with `missing_contact_detail`; expect incomplete-record detection.
5. Run CRM update with an approved discount; verify the UI confirmation and corresponding RPA outcome record.

