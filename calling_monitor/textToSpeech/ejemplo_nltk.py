import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Asegúrate de tener estos recursos descargados
nltk.data.find('tokenizers/punkt')
nltk.data.find('corpora/stopwords')

# Texto de ejemplo
texto = "Este es un ejemplo simple para probar NLTK con Python."

# Tokenizar el texto
# tokens = word_tokenize(texto, language='spanish')
tokens = word_tokenize(texto)
print("Tokens:", tokens)

# Obtener palabras vacías en español
stop_words = set(stopwords.words('spanish'))

# Filtrar palabras vacías
tokens_filtrados = [palabra for palabra in tokens if palabra.lower() not in stop_words]
print("Tokens filtrados:", tokens_filtrados)
