<<<<<<< HEAD
from core import database
from core.models import Partner, PartnerTransaction

print("Initialisation de la base de données...")
database.init_database()
print("Création des tables manquantes...")
database.Base.metadata.create_all(bind=database.engine)
print("Terminé.")
print("Terminé.")
=======
from core import database
from core.models import Partner, PartnerTransaction

print("Initialisation de la base de données...")
database.init_database()
print("Création des tables manquantes...")
database.Base.metadata.create_all(bind=database.engine)
print("Terminé.")
print("Terminé.")
>>>>>>> 82db04ae8fedc46dcf3ff9852f45b56e5f079848
