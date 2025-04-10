import io
import json
import speech_recognition as sr
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required

@csrf_exempt
def home_view(request):
    return JsonResponse({'message': 'Welcome to the home endpoint.'}, status=200)


@csrf_exempt
def about_view(request):
    return JsonResponse({'message': 'This is the about endpoint.'}, status=200)


@csrf_exempt
def contact_view(request):
    return JsonResponse({'message': 'This is the contact endpoint.'}, status=200)


@csrf_exempt
@login_required(login_url="login")
def animation_view(request):
    if request.method == 'POST':
        #check if an audio file is provided
        if 'audio_file' in request.FILES:
            audio_file = request.FILES['audio_file']
            r = sr.Recognizer() #use speech recognition to extract text from the audio file
            try:
                #read file into an AudioFile object
                with sr.AudioFile(io.BytesIO(audio_file.read())) as source:
                    audio = r.record(source)
                text = r.recognize_google(audio)
            except Exception as e:
                return JsonResponse({'error': f'Error processing audio file: {str(e)}'}, status=400)
        # else use the text provided in the request body
        else:
            try:
                data = json.loads(request.body)
            except Exception as e:
                return JsonResponse({'error': 'Invalid JSON provided.'}, status=400)

            text = data.get('sen', '')
            if not text:
                return JsonResponse({'error': 'Missing "sen" parameter.'}, status=400)

        # Convert text to lowercase
        text = text.lower()

        # Tokenize the sentence
        words = word_tokenize(text)
        tagged = nltk.pos_tag(words)

        # Determine tense counts
        tense = {
            "future": len([word for word in tagged if word[1] == "MD"]),
            "present": len([word for word in tagged if word[1] in ["VBP", "VBZ", "VBG"]]),
            "past": len([word for word in tagged if word[1] in ["VBD", "VBN"]]),
            "present_continuous": len([word for word in tagged if word[1] == "VBG"])
        }

        # Define custom stopwords
        stop_words = set([
            "mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",
            'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its',
            "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is',
            'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's",
            "needn't", 'd', 'am', 'have', 'hasn', 'o', "aren't", "you'll", "couldn't", "you're",
            "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself',
            'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren',
            'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"
        ])

        # Removing stopwords and applying lemmatization
        lr = WordNetLemmatizer()
        filtered_text = []
        for w, pos in zip(words, tagged):
            if w not in stop_words:
                if pos[1] in ['VBG', 'VBD', 'VBZ', 'VBN', 'NN']:
                    filtered_text.append(lr.lemmatize(w, pos='v'))
                elif pos[1] in ['JJ', 'JJR', 'JJS', 'RBR', 'RBS']:
                    filtered_text.append(lr.lemmatize(w, pos='a'))
                else:
                    filtered_text.append(lr.lemmatize(w))
        words = filtered_text

        # Post-processing: adjust specific words
        words = ['Me' if w == 'i' else w for w in words]

        # Determine the most probable tense and add a marker word if needed
        probable_tense = max(tense, key=tense.get)
        if probable_tense == "past" and tense["past"] >= 1:
            words = ["Before"] + words
        elif probable_tense == "future" and tense["future"] >= 1:
            if "Will" not in words:
                words = ["Will"] + words
        elif probable_tense == "present" and tense["present_continuous"] >= 1:
            words = ["Now"] + words

        # For each word, check for a corresponding ".mp4" file in your static files.
        final_words = []
        for w in words:
            path = w + ".mp4"
            f = finders.find(path)
            if not f:
                # if file not found, split word into characters
                final_words.extend(list(w))
            else:
                final_words.append(w)

        return JsonResponse({'words': final_words, 'text': text}, status=200)

    # for get or other requests, a simple message is returned
    return JsonResponse({'message': 'Send a POST request with JSON payload {"sen": "your sentence"}'}, status=200)


@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception as e:
            return JsonResponse({'error': 'Invalid JSON provided.'}, status=400)

        form = UserCreationForm(data)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'message': 'User registered successfully.'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'message': 'Send a POST request with user registration data.'}, status=200)


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception as e:
            return JsonResponse({'error': 'Invalid JSON provided.'}, status=400)

        form = AuthenticationForm(request, data=data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return JsonResponse({'message': 'Logged in successfully.'}, status=200)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'message': 'Send a POST request with login credentials.'}, status=200)


@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully.'}, status=200)
