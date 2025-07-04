from db_AN.database_AN import SessionLocal
from models_AN.subscription_model_AN import Subscription_AN

db = SessionLocal()
sub = db.query(Subscription_AN).first()
sub.schedule_hash = "MANUAL_EDIT_TEST_HASH4у34"
db.commit()
db.close()

print("✅ Hash został zmieniony!")
