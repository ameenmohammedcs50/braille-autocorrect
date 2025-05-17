from flask import Flask, render_template, request, jsonify
from english_words import get_english_words_set

app = Flask(__name__)

# Load dictionary
dictionary = list(get_english_words_set(sources=["web2"]))
print(f"Loaded {len(dictionary)} words")

# QWERTY to Braille dot mapping
key_to_dot = {
    'd': '1',
    'w': '2',
    'q': '3',
    'k': '4',
    'o': '5',
    'p': '6'
}

# Braille patterns
braille_to_char_map = {
    '1': 'a',     '12': 'b',     '14': 'c',     '145': 'd',    '15': 'e',
    '124': 'f',   '1245': 'g',   '125': 'h',    '24': 'i',     '245': 'j',
    '13': 'k',    '123': 'l',    '134': 'm',    '1345': 'n',   '135': 'o',
    '1234': 'p',  '12345': 'q',  '1235': 'r',   '234': 's',    '2345': 't',
    '136': 'u',   '1236': 'v',   '2456': 'w',   '1346': 'x',   '13456': 'y',
    '1356': 'z'
}

def levenshtein(a, b):
    dp = [[0] * (len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)+1):
        dp[i][0] = i
    for j in range(len(b)+1):
        dp[0][j] = j
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
    return dp[-1][-1]

def suggest_word(input_word, dictionary):
    input_word = input_word.lower()
    best_match = None
    min_distance = float('inf')
    for word in dictionary:
        dist = levenshtein(input_word, word.lower())
        if dist < min_distance:
            min_distance = dist
            best_match = word
    return best_match

def decode_braille_sequence(sequence):
    chars = []
    errors = []
    for group in sequence.strip().split():
        dots = sorted([key_to_dot.get(char.lower()) for char in group if char.lower() in key_to_dot])
        if None in dots or not dots:
            chars.append('?')
            errors.append(group)
            continue
        dot_str = ''.join(dots)
        if dot_str in braille_to_char_map:
            chars.append(braille_to_char_map[dot_str])
        else:
            chars.append('?')
            errors.append(group)
    return ''.join(chars), errors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suggest', methods=['POST'])
def suggest():
    data = request.get_json()
    typed_seq = data.get('word', '')
    decoded_word, errors = decode_braille_sequence(typed_seq)
    suggestion = suggest_word(decoded_word.replace('?', ''), dictionary)
    return jsonify({
        'typed_sequence': typed_seq,
        'decoded_word': decoded_word,
        'suggestion': suggestion,
        'errors': errors
    })

if __name__ == '__main__':
    # Allow access from all IPs (important for deployment or non-local use)
    app.run(debug=True, host='0.0.0.0', port=5000)

