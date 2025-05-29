import unittest
import pandas as pd
import mysql.connector
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock de tkinter para evitar problemas en las pruebas
sys.modules['tkinter'] = Mock()
sys.modules['tkinter.ttk'] = Mock()
sys.modules['tkinter.simpledialog'] = Mock()
sys.modules['tkinter.messagebox'] = Mock()
sys.modules['tkinter.filedialog'] = Mock()

# Importar las funciones después del mock
import prototipo

class TestSistemaRecomendaciones(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Mock de la conexión a la base de datos
        self.mock_cnx = Mock()
        self.mock_cursor = Mock()
        self.mock_cursor.fetchone.return_value = {'username': 'testuser', 'password': 'testpass'}
        self.mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'TrackName': 'Test Song',
                'ArtistName': 'Test Artist',
                'Genres': 'Pop',
                'Danceability': 0.7,
                'Energy': 0.6,
                'Key': 5,
                'Loudness': -5.0,
                'Mode': 1,
                'Speechiness': 0.1,
                'Acousticness': 0.2,
                'Instrumentalness': 0.0,
                'Liveness': 0.1,
                'Valence': 0.8,
                'Tempo': 120.0
            }
        ]
        
        # Datos de prueba para playlist
        self.test_playlist = pd.DataFrame({
            'Track Name': ['Song 1', 'Song 2'],
            'Artist Name': ['Artist 1', 'Artist 2'],
            'Danceability': [0.8, 0.6],
            'Energy': [0.7, 0.5],
            'Key': [4, 6],
            'Loudness': [-4.0, -6.0],
            'Mode': [1, 0],
            'Speechiness': [0.05, 0.15],
            'Acousticness': [0.1, 0.3],
            'Instrumentalness': [0.0, 0.01],
            'Liveness': [0.2, 0.1],
            'Valence': [0.9, 0.7],
            'Tempo': [125.0, 110.0]
        })

    def test_confirmar_usuario_existente(self):
        """Prueba que confirmar() detecte usuarios existentes"""
        with patch('prototipo.cursor', self.mock_cursor):
            self.mock_cursor.fetchone.return_value = {'username': 'testuser'}
            resultado = prototipo.confirmar('testuser')
            self.assertTrue(resultado)
            
    def test_confirmar_usuario_no_existente(self):
        """Prueba que confirmar() detecte usuarios no existentes"""
        with patch('prototipo.cursor', self.mock_cursor):
            self.mock_cursor.fetchone.return_value = None
            resultado = prototipo.confirmar('noexiste')
            self.assertFalse(resultado)

    def test_verificar_credenciales_correctas(self):
        """Prueba verificación de credenciales correctas"""
        with patch('prototipo.cursor', self.mock_cursor):
            self.mock_cursor.fetchone.return_value = {'username': 'testuser', 'password': 'testpass'}
            resultado = prototipo.verificar('testuser', 'testpass')
            self.assertTrue(resultado)

    def test_verificar_credenciales_incorrectas(self):
        """Prueba verificación de credenciales incorrectas"""
        with patch('prototipo.cursor', self.mock_cursor):
            self.mock_cursor.fetchone.return_value = None
            resultado = prototipo.verificar('testuser', 'wrongpass')
            self.assertFalse(resultado)

    def test_none_function_with_nan(self):
        """Prueba la función none() con valores NaN"""
        import math
        resultado = prototipo.none(float('nan'))
        self.assertIsNone(resultado)

    def test_none_function_with_empty_string(self):
        """Prueba la función none() con string vacío"""
        resultado = prototipo.none('   ')
        self.assertIsNone(resultado)

    def test_none_function_with_valid_value(self):
        """Prueba la función none() con valor válido"""
        resultado = prototipo.none('valid_value')
        self.assertEqual(resultado, 'valid_value')

    @patch('prototipo.cursor')
    @patch('prototipo.cnx')
    def test_crear_tabla_recomendaciones(self, mock_cnx, mock_cursor):
        """Prueba la creación de la tabla de recomendaciones"""
        prototipo.crear_tabla_recomendaciones()
        mock_cursor.execute.assert_called_once()
        mock_cnx.commit.assert_called_once()

    @patch('prototipo.cursor')
    @patch('prototipo.cnx')
    def test_guardar_recomendaciones(self, mock_cnx, mock_cursor):
        """Prueba el guardado de recomendaciones"""
        # Crear DataFrame de prueba para recomendaciones
        recommendations = pd.DataFrame({
            'TrackName': ['Test Track'],
            'ArtistName': ['Test Artist'],
            'Genres': ['Pop'],
            'Distance': [0.5]
        })
        
        prototipo.guardar_recomendaciones(recommendations, 'testuser')
        
        # Verificar que se ejecutaron las consultas
        self.assertTrue(mock_cursor.execute.called)
        mock_cnx.commit.assert_called()

    @patch('prototipo.cursor')
    def test_obtener_recomendaciones_guardadas(self, mock_cursor):
        """Prueba la obtención de recomendaciones guardadas"""
        mock_cursor.fetchall.return_value = [
            {
                'track_name': 'Test Track',
                'artist_name': 'Test Artist',
                'genres': 'Pop',
                'distance': 0.5,
                'recommendation_date': '2024-01-01 12:00:00'
            }
        ]
        
        resultado = prototipo.obtener_recomendaciones_guardadas('testuser')
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['track_name'], 'Test Track')

    def test_playlist_data_cleaning(self):
        """Prueba la limpieza de datos de playlist"""
        # Crear DataFrame con datos faltantes
        dirty_playlist = self.test_playlist.copy()
        dirty_playlist.loc[0, 'Danceability'] = None
        
        categorias = [
            'Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
            'Speechiness', 'Acousticness', 'Instrumentalness',
            'Liveness', 'Valence', 'Tempo'
        ]
        
        clean_playlist = dirty_playlist.dropna(subset=categorias)
        
        # Verificar que se eliminó la fila con datos faltantes
        self.assertEqual(len(clean_playlist), 1)

    def test_vector_promedio_calculation(self):
        """Prueba el cálculo del vector promedio"""
        categorias = [
            'Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
            'Speechiness', 'Acousticness', 'Instrumentalness',
            'Liveness', 'Valence', 'Tempo'
        ]
        
        vector_promedio = self.test_playlist[categorias].mean().values
        
        # Verificar que el vector tiene la longitud correcta
        self.assertEqual(len(vector_promedio), len(categorias))
        
        # Verificar algunos valores esperados
        self.assertAlmostEqual(vector_promedio[0], 0.7, places=1)  # Danceability promedio

class TestIntegrationDatabase(unittest.TestCase):
    """Pruebas de integración con base de datos (requiere MySQL corriendo)"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración para toda la clase de pruebas"""
        try:
            cls.cnx = mysql.connector.connect(
                host='localhost',
                user='admin',
                password='123',
                database='login'
            )
            cls.cursor = cls.cnx.cursor(dictionary=True)
            cls.db_available = True
        except mysql.connector.Error:
            cls.db_available = False
            
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        if cls.db_available:
            cls.cursor.close()
            cls.cnx.close()

    def setUp(self):
        """Configuración para cada prueba"""
        if not self.db_available:
            self.skipTest("Base de datos no disponible")

    def test_database_connection(self):
        """Prueba la conexión a la base de datos"""
        self.assertTrue(self.cnx.is_connected())

    def test_users_table_exists(self):
        """Prueba que la tabla users existe"""
        self.cursor.execute("SHOW TABLES LIKE 'users'")
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)

    def test_songs_table_exists(self):
        """Prueba que la tabla songs existe"""
        self.cursor.execute("SHOW TABLES LIKE 'songs'")
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)

    def test_insert_and_delete_test_user(self):
        """Prueba inserción y eliminación de usuario de prueba"""
        # Insertar usuario de prueba
        test_username = 'unittest_user'
        test_password = 'unittest_pass'
        
        # Limpiar usuario de prueba si existe
        self.cursor.execute("DELETE FROM users WHERE username = %s", (test_username,))
        
        # Insertar nuevo usuario
        self.cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (test_username, test_password)
        )
        self.cnx.commit()
        
        # Verificar inserción
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (test_username,))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], test_username)
        
        # Limpiar
        self.cursor.execute("DELETE FROM users WHERE username = %s", (test_username,))
        self.cnx.commit()

class TestRecommendationSystem(unittest.TestCase):
    """Pruebas del sistema de recomendaciones"""
    
    def test_euclidean_distance_calculation(self):
        """Prueba el cálculo de distancia euclidiana"""
        from sklearn.metrics.pairwise import euclidean_distances
        import numpy as np
        
        vector1 = np.array([[1, 2, 3]])
        vector2 = np.array([[4, 5, 6]])
        
        distance = euclidean_distances(vector1, vector2)[0][0]
        expected_distance = np.sqrt((4-1)**2 + (5-2)**2 + (6-3)**2)
        
        self.assertAlmostEqual(distance, expected_distance, places=5)

    def test_graph_creation(self):
        """Prueba la creación del grafo"""
        import networkx as nx
        
        G = nx.Graph()
        G.add_node("avg")
        G.add_node(1, TrackName="Test", ArtistName="Artist")
        G.add_edge("avg", 1, weight=0.5)
        
        self.assertIn("avg", G.nodes())
        self.assertIn(1, G.nodes())
        self.assertEqual(G["avg"][1]['weight'], 0.5)

def run_tests():
    """Función para ejecutar todas las pruebas"""
    # Crear suite de pruebas
    suite = unittest.TestSuite()
    
    # Agregar pruebas unitarias
    suite.addTest(unittest.makeSuite(TestSistemaRecomendaciones))
    suite.addTest(unittest.makeSuite(TestRecommendationSystem))
    
    # Agregar pruebas de integración solo si están disponibles
    try:
        mysql.connector.connect(
            host='localhost',
            user='admin',
            password='123',
            database='login'
        ).close()
        suite.addTest(unittest.makeSuite(TestIntegrationDatabase))
        print("✓ Pruebas de integración con base de datos incluidas")
    except:
        print("⚠ Pruebas de integración omitidas (base de datos no disponible)")
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFALLOS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORES:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # Ejecutar pruebas
    success = run_tests()
    exit(0 if success else 1)