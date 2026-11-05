from core.database import DB_PATH,query
def status():
    try:return {"connected":True,"database":str(DB_PATH),"opportunities":query("SELECT COUNT(*) n FROM sales_opportunities")[0]["n"]}
    except Exception as exc:return {"connected":False,"error":str(exc)}

