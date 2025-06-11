## Requisitos

### Compressores

Os seguintes compressores são necessários:
- gzip
- bzip2
- lzma 
- zstd

## Instalação

1. Clone este repositório
   ```
   git clone https://github.com/andreaoliveira9/Projeto-TAI-3.git
   cd src
   ```

2. Crie um ambiente virtual
   ```
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. Instale os pacotes Python necessários
   ```
   pip install -r requirements.txt
   ```

## Executando o Demo (demo.ipynb)

O notebook `demo.ipynb` fornece uma demonstração completa do sistema de identificação musical. Para executá-lo:

1. Certifique-se de que todas as dependências estão instaladas
2. Coloque a música que pretende identificar em `demo_music`
3. Execute as células do notebook em sequência para:
   - Converter arquivo de música em representações de frequência
   - Extrair segmentos de músicas (opcional)
   - Adicionar ruído aos segmentos (opcional)
   - Converter segmentos em representações de frequência
   - Identificar música comparando o segmento com o banco de dados

## Estrutura de Diretórios

- `/database`: Contém representações de frequência de arquivos de música
- `/segments`: Contém segmentos extraídos para teste
- `/demo_music`: Contém arquivo de música para demonstração
- `/demo_segments`: Contém segmentos extraídos para demonstração
- `evaluate_compressors.py`: Script para avaliar diferentes compressores
- `audio_processing.py`: Funções para manipulação de áudio
- `feature_extraction.py`: Funções para converter áudio em características de frequência
- `ncd.py`: Funções para cálculo de NCD
- `music_identification.py`: Funções para identificação musical
- `main.py`: Interface de linha de comando principal
- `demo.ipynb`: Notebook Jupyter para demonstração do sistema

## Músicas de teste

URL: https://filesender.fccn.pt/?s=download&token=141af58e-6b32-4826-a84d-777097c0b377

## Referências

Rudi Cilibrasi, Paul Vitányi, and Ronald de Wolf, *Algorithmic Clustering of Music Based on String Compression*, Computer Music Journal, 28:4, pp. 49–67, 2004.
