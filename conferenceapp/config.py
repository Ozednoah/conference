class Config(object):
    DATABASE_URI='some random parameters'
    MERCHANT_ID="SAMPLE"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI="mysql+mysqlconnector://root@localhost/confdb"

class TestConfig(Config):
    DATABASE_URI="test connection parameters"
