import sqlite3

def open_db(path: str) -> sqlite3.Connection | None:
    try:
        conn = sqlite3.connect(path)
    except Exception as e:
        print(f"Unable to open database because of '{e}'")
        return None
    
    cur = conn.cursor()
    if not ensure_tables(cur):
        return None
    
    return conn

def ensure_tables(cur: sqlite3.Cursor) -> bool:
    try:
        cur.executescript("""
                    CREATE TABLE IF NOT EXISTS USERS (
                        U_ID INTEGER PRIMARY KEY,
                        USERNAME TEXT NOT NULL, 
                        F_NAME TEXT NOT NULL,
                        L_NAME TEXT NOT NULL,
                        PASSWD TEXT NOT NULL,
                        CONSTRAINT NAMES UNIQUE (F_NAME, L_NAME)
                    );

                    CREATE TABLE IF NOT EXISTS USER_SESSIONS (
                        U_ID INTEGER PRIMARY KEY,
                        JWT TEXT NOT NULL,
                        AT_TIME INTEGER NOT NULL,
                        
                        FOREIGN KEY (U_ID) REFERENCES USERS (U_ID) on delete cascade on update cascade
                    );

                    CREATE TABLE IF NOT EXISTS NODES (
                        N_ID INTEGER PRIMARY KEY,
                        X REAL NOT NULL,
                        Y REAL NOT NULL,
                        NODE_NAME TEXT,
                        NODE_GROUP TEXT DEFAULT NULL,
                        IS_PATH INTEGER
                        
                        CONSTRAINT NODE_KIND CHECK (IS_PATH IN (0, 1))
                    );

                    CREATE TABLE IF NOT EXISTS NODE_TAGS (
                        TAG_ID INTEGER PRIMARY KEY,
                        N_ID INTEGER NOT NULL,
                        TAG TEXT NOT NULL,
                        
                        FOREIGN KEY (N_ID) REFERENCES NODES (N_ID) ON DELETE CASCADE ON UPDATE CASCADE
                        CONSTRAINT ONE_TAG UNIQUE (N_ID, TAG)
                    );

                    CREATE TABLE IF NOT EXISTS EDGES (
                        SOURCE INTEGER NOT NULL,
                        DESTIONATION INTEGER NOT NULL,

                        CONSTRAINT PK1 PRIMARY KEY (SOURCE, DESTIONATION),

                        FOREIGN KEY (SOURCE) REFERENCES NODES (N_ID) ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY (DESTIONATION) REFERENCES NODES (N_ID) ON DELETE CASCADE ON UPDATE CASCADE
                    );
                    """)
        
        return True
    except:
        return False
