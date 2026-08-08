"""
Sample User Stories and Bugs for EQIP — Engineering Quality Intelligence Platform.

This module provides realistic sample data representing a typical sprint in an
e-commerce platform project.  The data is used by test cases and can also serve
as reference documentation for how the EQIP data model maps to real delivery
artefacts.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Sample User Stories
# ---------------------------------------------------------------------------

SAMPLE_USER_STORIES = [
    {
        "story_id": "US-101",
        "title": "User Login with Email and Password",
        "epic": "Authentication",
        "module": "Auth",
        "priority": "High",
        "complexity": "Medium",
        "story_points": 5,
        "status": "done",
        "acceptance_criteria": (
            "1. User can log in with valid email/password.\n"
            "2. Show error for invalid credentials.\n"
            "3. Lock account after 5 failed attempts.\n"
            "4. Session token expires after 30 minutes of inactivity."
        ),
    },
    {
        "story_id": "US-102",
        "title": "Product Search with Filters",
        "epic": "Catalog",
        "module": "Search",
        "priority": "High",
        "complexity": "High",
        "story_points": 8,
        "status": "done",
        "acceptance_criteria": (
            "1. Search by product name returns relevant results.\n"
            "2. Filter by category, price range, and rating.\n"
            "3. Results paginated (20 per page).\n"
            "4. No results shows a friendly empty state."
        ),
    },
    {
        "story_id": "US-103",
        "title": "Add to Cart and Update Quantity",
        "epic": "Cart",
        "module": "Cart",
        "priority": "High",
        "complexity": "Medium",
        "story_points": 5,
        "status": "done",
        "acceptance_criteria": (
            "1. User can add a product to cart.\n"
            "2. Quantity can be incremented/decremented.\n"
            "3. Cart total updates in real time.\n"
            "4. Out-of-stock products cannot be added."
        ),
    },
    {
        "story_id": "US-104",
        "title": "Checkout with Stripe Payment",
        "epic": "Payments",
        "module": "Checkout",
        "priority": "Critical",
        "complexity": "High",
        "story_points": 13,
        "status": "in_progress",
        "acceptance_criteria": (
            "1. User completes checkout with credit card via Stripe.\n"
            "2. Order confirmation email sent on success.\n"
            "3. Payment failure shows retry option.\n"
            "4. Inventory decremented atomically on payment success."
        ),
    },
    {
        "story_id": "US-105",
        "title": "Order History and Tracking",
        "epic": "Orders",
        "module": "Orders",
        "priority": "Medium",
        "complexity": "Medium",
        "story_points": 5,
        "status": "in_testing",
        "acceptance_criteria": (
            "1. User sees list of past orders sorted by date.\n"
            "2. Each order shows status (placed, shipped, delivered).\n"
            "3. Tracking link opens carrier page.\n"
            "4. Filter orders by date range."
        ),
    },
    {
        "story_id": "US-106",
        "title": "User Profile Management",
        "epic": "User Management",
        "module": "Profile",
        "priority": "Medium",
        "complexity": "Low",
        "story_points": 3,
        "status": "done",
        "acceptance_criteria": (
            "1. User can update name, email, and phone.\n"
            "2. Email change requires verification.\n"
            "3. Password change requires current password.\n"
            "4. Profile photo upload (max 5 MB, JPG/PNG)."
        ),
    },
    {
        "story_id": "US-107",
        "title": "Admin Dashboard — Sales Analytics",
        "epic": "Admin",
        "module": "Analytics",
        "priority": "Low",
        "complexity": "High",
        "story_points": 8,
        "status": "backlog",
        "acceptance_criteria": (
            "1. Dashboard shows daily/weekly/monthly revenue.\n"
            "2. Top 10 products by sales volume chart.\n"
            "3. Export data as CSV.\n"
            "4. Date range filter with preset shortcuts."
        ),
    },
    {
        "story_id": "US-108",
        "title": "Push Notification Preferences",
        "epic": "Notifications",
        "module": "Notifications",
        "priority": "Low",
        "complexity": "Low",
        "story_points": 3,
        "status": "done",
        "acceptance_criteria": (
            "1. User can enable/disable push notifications.\n"
            "2. Granular control per category (orders, promos, security).\n"
            "3. Changes take effect immediately.\n"
            "4. Default: all enabled for new users."
        ),
    },
    {
        "story_id": "US-109",
        "title": "Wishlist Functionality",
        "epic": "Catalog",
        "module": "Wishlist",
        "priority": "Medium",
        "complexity": "Low",
        "story_points": 3,
        "status": "done",
        "acceptance_criteria": (
            "1. User can add/remove products to/from wishlist.\n"
            "2. Wishlist persists across sessions.\n"
            "3. 'Move to cart' button on each wishlist item.\n"
            "4. Max 50 items in wishlist."
        ),
    },
    {
        "story_id": "US-110",
        "title": "Password Reset via Email",
        "epic": "Authentication",
        "module": "Auth",
        "priority": "High",
        "complexity": "Medium",
        "story_points": 5,
        "status": "done",
        "acceptance_criteria": (
            "1. User requests password reset with registered email.\n"
            "2. Reset link valid for 15 minutes.\n"
            "3. Link is single-use.\n"
            "4. Success confirmation shown after reset."
        ),
    },
]

# ---------------------------------------------------------------------------
# Sample Bugs
# ---------------------------------------------------------------------------

SAMPLE_BUGS = [
    {
        "bug_id": "BUG-201",
        "story_id": "US-101",
        "summary": "Login allows SQL injection in email field",
        "description": (
            "The email field on the login page does not sanitize input. "
            "Entering `' OR 1=1 --` bypasses authentication."
        ),
        "severity": "critical",
        "priority": "P0",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "security",
        "origin_stage": "development",
        "status": "fixed",
    },
    {
        "bug_id": "BUG-202",
        "story_id": "US-101",
        "summary": "Account lockout counter resets on page refresh",
        "description": (
            "After 4 failed login attempts, refreshing the page resets the "
            "counter, allowing unlimited retries."
        ),
        "severity": "high",
        "priority": "P1",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "validation",
        "origin_stage": "development",
        "status": "fixed",
    },
    {
        "bug_id": "BUG-203",
        "story_id": "US-102",
        "summary": "Price filter returns products outside selected range",
        "description": (
            "Filtering products by price $10–$50 also returns products priced "
            "at $0 and above $50 due to off-by-one boundary error."
        ),
        "severity": "medium",
        "priority": "P2",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "validation",
        "origin_stage": "development",
        "status": "open",
    },
    {
        "bug_id": "BUG-204",
        "story_id": "US-102",
        "summary": "Search returns 500 error for special characters",
        "description": (
            "Searching for `<script>alert(1)</script>` returns a 500 internal "
            "server error instead of zero results."
        ),
        "severity": "high",
        "priority": "P1",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "validation",
        "origin_stage": "development",
        "status": "fixed",
    },
    {
        "bug_id": "BUG-205",
        "story_id": "US-103",
        "summary": "Cart allows adding more items than available stock",
        "description": (
            "User can set cart quantity to 999 even when only 5 items are in "
            "stock. Inventory validation is missing on the frontend."
        ),
        "severity": "high",
        "priority": "P1",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "validation",
        "origin_stage": "requirement",
        "status": "open",
    },
    {
        "bug_id": "BUG-206",
        "story_id": "US-103",
        "summary": "Cart total shows wrong amount with discount code",
        "description": (
            "When a 20% discount code is applied, the cart total subtracts "
            "20% from each item individually instead of the grand total, "
            "resulting in a different final amount."
        ),
        "severity": "critical",
        "priority": "P0",
        "environment": "UAT",
        "detected_stage": "uat",
        "root_cause_category": "business_logic",
        "origin_stage": "requirement",
        "status": "open",
    },
    {
        "bug_id": "BUG-207",
        "story_id": "US-104",
        "summary": "Double charge when user clicks Pay button twice",
        "description": (
            "Rapidly clicking the Pay button submits two payment requests to "
            "Stripe, resulting in a double charge."
        ),
        "severity": "critical",
        "priority": "P0",
        "environment": "Staging",
        "detected_stage": "staging",
        "root_cause_category": "validation",
        "origin_stage": "development",
        "status": "open",
    },
    {
        "bug_id": "BUG-208",
        "story_id": "US-104",
        "summary": "Order confirmation email not sent for guest checkout",
        "description": (
            "Guest users who complete checkout do not receive an order "
            "confirmation email. The email service skips users without "
            "an account."
        ),
        "severity": "medium",
        "priority": "P2",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "requirement_gap",
        "origin_stage": "requirement",
        "status": "open",
    },
    {
        "bug_id": "BUG-209",
        "story_id": "US-105",
        "summary": "Order history page crashes for users with 1000+ orders",
        "description": (
            "Loading order history for power users with over 1000 orders "
            "causes the page to crash. No pagination on the API query."
        ),
        "severity": "high",
        "priority": "P1",
        "environment": "Production",
        "detected_stage": "production",
        "root_cause_category": "performance",
        "origin_stage": "development",
        "status": "open",
    },
    {
        "bug_id": "BUG-210",
        "story_id": "US-106",
        "summary": "Profile photo upload accepts files larger than 5 MB",
        "description": (
            "The file-size limit of 5 MB is only enforced on the frontend. "
            "Uploading via API allows files up to 100 MB."
        ),
        "severity": "medium",
        "priority": "P2",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "validation",
        "origin_stage": "development",
        "status": "fixed",
    },
    {
        "bug_id": "BUG-211",
        "story_id": "US-110",
        "summary": "Password reset link can be reused multiple times",
        "description": (
            "The acceptance criteria state the reset link should be single-use, "
            "but the token is not invalidated after first use."
        ),
        "severity": "high",
        "priority": "P1",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "security",
        "origin_stage": "development",
        "status": "fixed",
    },
    {
        "bug_id": "BUG-212",
        "story_id": "US-109",
        "summary": "Wishlist does not enforce 50-item limit",
        "description": (
            "Users can add more than 50 items to their wishlist. The "
            "acceptance criteria specify a maximum of 50."
        ),
        "severity": "medium",
        "priority": "P2",
        "environment": "QA",
        "detected_stage": "qa_testing",
        "root_cause_category": "acceptance_criteria_missing",
        "origin_stage": "development",
        "status": "open",
    },
]
