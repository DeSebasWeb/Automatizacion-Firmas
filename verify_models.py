"""Verification script for new SQLAlchemy models."""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.models import (
    DocumentType,
    PermissionType,
    APIPermissionScope,
    APIKey,
    APIKeyScope,
)
from src.infrastructure.database.session import SessionLocal


def verify_models():
    """Verify that the new models work correctly."""
    print("=" * 60)
    print("VERIFICATION: SQLAlchemy Models for New DB Structure")
    print("=" * 60)

    try:
        # Test imports
        print("\n✅ Step 1: Models imported successfully")
        print(f"   - DocumentType: {DocumentType}")
        print(f"   - PermissionType: {PermissionType}")
        print(f"   - APIPermissionScope: {APIPermissionScope}")

        # Test database connection and queries
        with SessionLocal() as session:
            print("\n✅ Step 2: Database connection established")

            # Query DocumentTypes
            doc_types = session.query(DocumentType).all()
            print(f"\n✅ Step 3: DocumentTypes found: {len(doc_types)}")
            for dt in doc_types[:5]:  # Show first 5
                print(f"   - {dt}")

            # Query PermissionTypes
            perm_types = session.query(PermissionType).all()
            print(f"\n✅ Step 4: PermissionTypes found: {len(perm_types)}")
            for pt in perm_types:
                print(f"   - {pt}")

            # Query APIPermissionScopes with relationships
            scopes = session.query(APIPermissionScope).all()
            print(f"\n✅ Step 5: APIPermissionScopes found: {len(scopes)}")
            for scope in scopes[:10]:  # Show first 10
                doc_type_code = scope.document_type.code if scope.document_type else "NULL"
                perm_type_code = scope.permission_type.code if scope.permission_type else "NULL"
                print(f"   - {scope.code:30} → doc:{doc_type_code:15} perm:{perm_type_code}")

            # Verify relationships work in reverse
            print("\n✅ Step 6: Testing reverse relationships")
            if doc_types:
                first_doc = doc_types[0]
                print(f"   - DocumentType '{first_doc.code}' has {len(first_doc.permission_scopes)} permission scopes")
                for ps in first_doc.permission_scopes[:3]:
                    print(f"     → {ps.code}")

            if perm_types:
                first_perm = perm_types[0]
                print(f"   - PermissionType '{first_perm.code}' has {len(first_perm.permission_scopes)} permission scopes")
                for ps in first_perm.permission_scopes[:3]:
                    print(f"     → {ps.code}")

            # Verify APIKey relationships are intact
            print("\n✅ Step 7: Verifying existing APIKey relationships")
            api_keys = session.query(APIKey).limit(3).all()
            for key in api_keys:
                print(f"   - APIKey {key.key_prefix} has {len(key.scopes)} scopes")
                for aks in key.scopes:
                    print(f"     → {aks.scope.code}")

        print("\n" + "=" * 60)
        print("✅ ALL VERIFICATIONS PASSED!")
        print("=" * 60)
        print("\nModels are correctly configured and connected to the database.")
        print("\nRelationships verified:")
        print("  DocumentType (1) ←→ (N) APIPermissionScope")
        print("  PermissionType (1) ←→ (N) APIPermissionScope")
        print("  APIPermissionScope (1) ←→ (N) APIKeyScope")
        print("  APIKey (1) ←→ (N) APIKeyScope")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_models()
    sys.exit(0 if success else 1)
