"""Quick test that Neo4j is running and supports vector search. Usage: python -m graphrag.check_neo4j"""
from neo4j import GraphDatabase

from graphrag import settings


def main():
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    driver.verify_connectivity()
    with driver.session() as s:
        info = s.run("CALL dbms.components() YIELD name, versions RETURN name, versions").data()
        print("Connected:", info[0]["name"], info[0]["versions"])
        procs = s.run("SHOW PROCEDURES YIELD name WHERE name = 'db.index.vector.queryNodes' RETURN name").data()
        print("Vector search available:", bool(procs))
    driver.close()


if __name__ == "__main__":
    main()
