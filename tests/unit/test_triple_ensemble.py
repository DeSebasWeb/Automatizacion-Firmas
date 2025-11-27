"""Tests unitarios para Triple Ensemble OCR y AWS Textract Adapter."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
import io

from src.domain.entities import CedulaRecord
from src.infrastructure.ocr.triple_ensemble_ocr import TripleEnsembleOCR, DigitVote, DigitConsensus


class TestAWSTextractAdapter:
    """Tests para AWS Textract Adapter."""

    @pytest.fixture
    def mock_config(self):
        """Mock de configuración."""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'image_preprocessing': {},
            'image_preprocessing.enabled': True,
            'ocr.aws_textract.max_retries': 3,
            'ocr.aws_textract.confidence_threshold': 0.85,
            'ocr.aws_textract.region': 'us-east-1',
            'ocr.aws_textract.access_key': 'test_key',
            'ocr.aws_textract.secret_key': 'test_secret',
        }.get(key, default))
        return config

    @patch('src.infrastructure.ocr.aws_textract_adapter.boto3')
    def test_aws_textract_initialization_with_credentials(self, mock_boto3, mock_config):
        """Verifica que se inicializa correctamente con credenciales explícitas."""
        from src.infrastructure.ocr.aws_textract_adapter import AWSTextractAdapter

        # Mock del cliente de boto3
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Inicializar adapter
        adapter = AWSTextractAdapter(mock_config)

        # Verificar que se creó el cliente con las credenciales correctas
        mock_boto3.client.assert_called_once_with(
            'textract',
            region_name='us-east-1',
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret'
        )

        assert adapter.client == mock_client
        assert adapter.region == 'us-east-1'

    @patch('src.infrastructure.ocr.aws_textract_adapter.boto3')
    def test_aws_textract_extract_numbers(self, mock_boto3, mock_config):
        """Verifica que extrae números correctamente desde respuesta de Textract."""
        from src.infrastructure.ocr.aws_textract_adapter import AWSTextractAdapter

        # Mock del cliente
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Mock de respuesta de Textract
        mock_response = {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': '1036221525',
                    'Confidence': 95.5
                },
                {
                    'BlockType': 'LINE',
                    'Text': '1234567890',
                    'Confidence': 92.3
                },
                {
                    'BlockType': 'WORD',  # Este debe ser ignorado
                    'Text': 'ignore',
                    'Confidence': 99.0
                }
            ]
        }
        mock_client.detect_document_text.return_value = mock_response

        # Inicializar adapter
        adapter = AWSTextractAdapter(mock_config)

        # Crear imagen de prueba
        test_image = Image.new('RGB', (100, 100), color='white')

        # Mock del preprocesador
        adapter.preprocess_image = Mock(return_value=test_image)

        # Ejecutar extracción
        records = adapter.extract_cedulas(test_image)

        # Verificar resultados
        assert len(records) == 2
        assert records[0].cedula.value == '1036221525'
        assert records[1].cedula.value == '1234567890'

    @patch('src.infrastructure.ocr.aws_textract_adapter.boto3')
    def test_aws_textract_get_character_confidences(self, mock_boto3, mock_config):
        """Verifica que retorna confianzas por carácter."""
        from src.infrastructure.ocr.aws_textract_adapter import AWSTextractAdapter

        # Mock del cliente
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        # Inicializar adapter
        adapter = AWSTextractAdapter(mock_config)

        # Mock de respuesta guardada
        adapter.last_raw_response = {
            'Blocks': [
                {
                    'BlockType': 'WORD',
                    'Text': '1036221525',
                    'Confidence': 95.5
                }
            ]
        }

        # Obtener confianzas
        result = adapter.get_character_confidences('1036221525')

        # Verificar estructura
        assert 'confidences' in result
        assert 'positions' in result
        assert 'average' in result
        assert 'source' in result
        assert result['source'] == 'aws_textract'
        assert len(result['confidences']) == 10  # 10 dígitos


class TestTripleEnsembleOCR:
    """Tests para Triple Ensemble OCR."""

    @pytest.fixture
    def mock_config(self):
        """Mock de configuración."""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'ocr.triple_ensemble.min_digit_confidence': 0.70,
            'ocr.triple_ensemble.low_confidence_threshold': 0.80,
            'ocr.triple_ensemble.min_agreement_ratio': 0.60,
            'ocr.triple_ensemble.verbose_logging': False,
        }.get(key, default))
        return config

    @pytest.fixture
    def mock_ocrs(self):
        """Mocks de los 3 OCR providers."""
        google = Mock()
        azure = Mock()
        aws = Mock()

        # Configurar preprocess_image
        google.preprocess_image = Mock(return_value=Image.new('RGB', (100, 100)))

        return google, azure, aws

    def test_triple_ensemble_initialization(self, mock_config, mock_ocrs):
        """Verifica que se inicializa correctamente con 3 OCR."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        assert ensemble.google_ocr == google
        assert ensemble.azure_ocr == azure
        assert ensemble.aws_ocr == aws
        assert ensemble.min_digit_confidence == 0.70
        assert ensemble.low_confidence_threshold == 0.80
        assert ensemble.min_agreement_ratio == 0.60

    def test_vote_single_digit_unanimous(self, mock_config, mock_ocrs):
        """Verifica votación unánime (los 3 coinciden)."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Los 3 reportan '5' con alta confianza
        consensus = ensemble._vote_single_digit(
            g_digit='5', g_conf=0.95,
            a_digit='5', a_conf=0.92,
            w_digit='5', w_conf=0.94,
            position=0
        )

        assert consensus.final_digit == '5'
        assert consensus.consensus_type == 'unanimous'
        assert consensus.agreement_count == 3
        # Debe tener boost de confianza (+5%, max 99.5%)
        assert consensus.confidence > 0.93

    def test_vote_single_digit_majority(self, mock_config, mock_ocrs):
        """Verifica votación por mayoría (2 de 3 coinciden)."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Google y AWS reportan '1', Azure reporta '7'
        consensus = ensemble._vote_single_digit(
            g_digit='1', g_conf=0.96,
            a_digit='7', a_conf=0.88,
            w_digit='1', w_conf=0.94,
            position=0
        )

        assert consensus.final_digit == '1'
        assert consensus.consensus_type == 'majority'
        assert consensus.agreement_count == 2
        # Confianza debe ser promedio de los 2 que coinciden
        assert 0.94 <= consensus.confidence <= 0.96

    def test_vote_single_digit_conflict(self, mock_config, mock_ocrs):
        """Verifica votación en conflicto (los 3 difieren)."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Los 3 reportan dígitos diferentes
        consensus = ensemble._vote_single_digit(
            g_digit='1', g_conf=0.85,
            a_digit='7', a_conf=0.82,
            w_digit='4', w_conf=0.88,
            position=0
        )

        # Debe elegir el de mayor confianza (AWS: '4' con 0.88)
        assert consensus.final_digit == '4'
        assert consensus.consensus_type == 'conflict'
        assert consensus.agreement_count == 1
        assert consensus.confidence == 0.88

    def test_vote_single_digit_low_confidence(self, mock_config, mock_ocrs):
        """Verifica manejo de baja confianza en conflicto."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Los 3 difieren y el mejor tiene confianza < 80%
        consensus = ensemble._vote_single_digit(
            g_digit='1', g_conf=0.65,
            a_digit='7', a_conf=0.70,
            w_digit='4', w_conf=0.75,
            position=0
        )

        # Debe elegir el mejor pero marcar como low_confidence
        assert consensus.final_digit == '4'
        assert consensus.consensus_type == 'low_confidence'
        assert consensus.confidence == 0.75

    def test_match_cedulas_in_triplets_by_position(self, mock_config, mock_ocrs):
        """Verifica que empareja cédulas por posición."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Crear registros de prueba
        google_records = [
            CedulaRecord.from_primitives('1036221525', 95.0),
            CedulaRecord.from_primitives('1234567890', 92.0),
        ]

        azure_records = [
            CedulaRecord.from_primitives('7036221525', 88.0),
            CedulaRecord.from_primitives('1234567890', 90.0),
        ]

        aws_records = [
            CedulaRecord.from_primitives('1036221525', 94.0),
            CedulaRecord.from_primitives('1234567890', 93.0),
        ]

        # Emparejar
        triplets = ensemble._match_cedulas_in_triplets(
            google_records,
            azure_records,
            aws_records
        )

        # Verificar emparejamiento por posición
        assert len(triplets) == 2

        # Triplete 1: posición 0
        assert triplets[0][0].cedula.value == '1036221525'  # Google
        assert triplets[0][1].cedula.value == '7036221525'  # Azure
        assert triplets[0][2].cedula.value == '1036221525'  # AWS

        # Triplete 2: posición 1
        assert triplets[1][0].cedula.value == '1234567890'  # Google
        assert triplets[1][1].cedula.value == '1234567890'  # Azure
        assert triplets[1][2].cedula.value == '1234567890'  # AWS

    def test_run_ocr_in_parallel(self, mock_config, mock_ocrs):
        """Verifica ejecución paralela de los 3 OCR."""
        google, azure, aws = mock_ocrs

        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Configurar mocks para retornar listas vacías
        google.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('1111111111', 95.0)
        ])
        azure.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('2222222222', 90.0)
        ])
        aws.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('3333333333', 92.0)
        ])

        # Crear imagen de prueba
        test_image = Image.new('RGB', (100, 100))

        # Ejecutar en paralelo
        google_records, azure_records, aws_records = ensemble._run_ocr_in_parallel(test_image)

        # Verificar que se llamaron los 3 OCR
        google.extract_cedulas.assert_called_once_with(test_image)
        azure.extract_cedulas.assert_called_once_with(test_image)
        aws.extract_cedulas.assert_called_once_with(test_image)

        # Verificar resultados
        assert len(google_records) == 1
        assert len(azure_records) == 1
        assert len(aws_records) == 1


class TestTripleEnsembleIntegration:
    """Tests de integración para el flujo completo."""

    @pytest.fixture
    def mock_config(self):
        """Mock de configuración."""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'ocr.triple_ensemble.min_digit_confidence': 0.70,
            'ocr.triple_ensemble.low_confidence_threshold': 0.80,
            'ocr.triple_ensemble.min_agreement_ratio': 0.60,
            'ocr.triple_ensemble.verbose_logging': False,
        }.get(key, default))
        return config

    def test_full_ensemble_flow_with_majority_voting(self, mock_config):
        """Test del flujo completo con votación por mayoría."""
        # Crear mocks de los 3 OCR
        google = Mock()
        azure = Mock()
        aws = Mock()

        # Configurar preprocess
        google.preprocess_image = Mock(return_value=Image.new('RGB', (100, 100)))

        # Configurar extract_cedulas
        google.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('1036221525', 96.0)  # Correcto
        ])
        azure.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('7036221525', 88.0)  # Error en primer dígito
        ])
        aws.extract_cedulas = Mock(return_value=[
            CedulaRecord.from_primitives('1036221525', 94.0)  # Correcto
        ])

        # Configurar get_character_confidences
        google.get_character_confidences = Mock(return_value={
            'confidences': [0.96] * 10,
            'positions': list(range(10)),
            'average': 0.96,
            'source': 'google_vision'
        })
        azure.get_character_confidences = Mock(return_value={
            'confidences': [0.88] * 10,
            'positions': list(range(10)),
            'average': 0.88,
            'source': 'azure_vision'
        })
        aws.get_character_confidences = Mock(return_value={
            'confidences': [0.94] * 10,
            'positions': list(range(10)),
            'average': 0.94,
            'source': 'aws_textract'
        })

        # Crear ensemble
        ensemble = TripleEnsembleOCR(
            config=mock_config,
            google_ocr=google,
            azure_ocr=azure,
            aws_ocr=aws
        )

        # Ejecutar extracción
        test_image = Image.new('RGB', (100, 100))
        records = ensemble.extract_cedulas(test_image)

        # Verificar resultado
        # Debería elegir '1036221525' porque Google + AWS coinciden (mayoría 2/3)
        assert len(records) == 1
        assert records[0].cedula.value == '1036221525'

        # La confianza debe ser alta (promedio de los que votaron)
        assert records[0].confidence.as_percentage() > 90.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
