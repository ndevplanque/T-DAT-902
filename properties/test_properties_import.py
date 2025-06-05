import unittest
from pyspark.sql import SparkSession
from csv_treatment import process_csv_file, get_schema

class PropertiesImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder \
            .master("local[*]") \
            .appName("TestImport") \
            .getOrCreate()

    def test_process_csv_file(self):
        sample_data = [
            ("2023-1", "2023-01-05", "000001", "Vente", "107000", "184", "", "0124", "ALL DES HETRES", "01630", "01354", "Saint-Genis", "", "", "01", "id123", "", "", "", "", "", "", "", "", "", "", "", "", "1", "2", "Appartement", "75", "3", "", "", "", "", "300", "6.02", "46.24"),
            ("2023-1", "2023-01-05", "000001", "Vente", "", "", "", "0124", "ALL DES HETRES", "01630", "01354", "Saint-Genis", "", "", "01", "id123", "", "", "", "", "", "", "", "", "", "", "", "", "1", "3", "Dépendance", "", "", "", "", "", "", "", "", "")
        ]
        schema = get_schema()
        df = self.spark.createDataFrame(sample_data, schema=schema)

        result = process_csv_file(self.spark, df)
        self.assertEqual(result.count(), 1)  # Une seule ligne valide

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

if __name__ == "__main__":
    unittest.main()
