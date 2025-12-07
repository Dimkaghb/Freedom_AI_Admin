"""
Test script to verify that company_id, department_id, and holding_id
are properly saved and returned for users registered via links.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.database import get_database
from src.settings import settings
from bson import ObjectId

def test_user_organization_ids():
    """Check if users have organization IDs saved"""
    print("=" * 70)
    print("  TESTING USER ORGANIZATION IDs")
    print("=" * 70)
    print()

    db = get_database()
    users_collection = db[settings.USERS_COLLECTION]
    pending_users_collection = db[settings.PENDING_USERS_COLLECTION]

    # Test 1: Check active users
    print("1. Checking Active Users:")
    print("-" * 70)
    users = list(users_collection.find().limit(5))

    if not users:
        print("   ⚠️  No users found in database")
    else:
        for i, user in enumerate(users, 1):
            print(f"   User {i}: {user.get('email')}")
            print(f"      - Role: {user.get('role')}")
            print(f"      - Company ID:    {user.get('company_id', 'NOT SET')}")
            print(f"      - Department ID: {user.get('department_id', 'NOT SET')}")
            print(f"      - Holding ID:    {user.get('holding_id', 'NOT SET')}")

            # Check if IDs are present
            has_company = bool(user.get('company_id'))
            has_holding = bool(user.get('holding_id'))

            if user.get('role') in ['admin', 'director', 'user']:
                if has_company:
                    print(f"      ✅ Has company_id")
                else:
                    print(f"      ❌ Missing company_id")

            if user.get('role') == 'superadmin':
                if has_holding:
                    print(f"      ✅ Has holding_id")

            print()

    # Test 2: Check pending users
    print("\n2. Checking Pending Users:")
    print("-" * 70)
    pending = list(pending_users_collection.find({"status": "pending"}).limit(5))

    if not pending:
        print("   ⚠️  No pending users found")
    else:
        for i, user in enumerate(pending, 1):
            print(f"   Pending User {i}: {user.get('email')}")
            print(f"      - Role: {user.get('role')}")
            print(f"      - Company ID:    {user.get('company_id', 'NOT SET')}")
            print(f"      - Department ID: {user.get('department_id', 'NOT SET')}")
            print(f"      - Holding ID:    {user.get('holding_id', 'NOT SET')}")
            print(f"      - Link ID: {user.get('link_id', 'NOT SET')}")

            has_company = bool(user.get('company_id'))
            if has_company:
                print(f"      ✅ Has company_id")
            else:
                print(f"      ❌ Missing company_id (BUG!)")
            print()

    # Test 3: Check registration links
    print("\n3. Checking Registration Links:")
    print("-" * 70)
    links_collection = db[settings.USER_LINKS_COLLECTION]
    links = list(links_collection.find().sort("created_at", -1).limit(5))

    if not links:
        print("   ⚠️  No registration links found")
    else:
        for i, link in enumerate(links, 1):
            print(f"   Link {i}:")
            print(f"      - Link ID: {link.get('link_id')}")
            print(f"      - Role: {link.get('role')}")
            print(f"      - Company ID:    {link.get('company_id', 'NOT SET')}")
            print(f"      - Department ID: {link.get('department_id', 'NOT SET')}")
            print(f"      - Holding ID:    {link.get('holding_id', 'NOT SET')}")
            print(f"      - Used: {link.get('is_used', False)}")
            print(f"      - Expired: {link.get('expires_at') < __import__('datetime').datetime.utcnow()}")
            print()

    print("=" * 70)
    print("\n✅ Test Complete!")
    print("\nExpected Behavior:")
    print("- Registration links should have company_id and holding_id")
    print("- Pending users should inherit IDs from the link")
    print("- Active users should have IDs after approval")
    print()

if __name__ == "__main__":
    try:
        test_user_organization_ids()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
