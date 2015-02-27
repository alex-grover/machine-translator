# machine-translator
Final project for Stanford CS 124. Translates Spanish sentences to English using Machine Translation techniques.

Required setup:
```bash
sudo pip install ntlk
python
>>> import nltk
>>> nltk.download()
```

And download all from the website.

To run on the dev set:
```bash
python code/translator.py dic/dict.txt corpus/dev.txt
```

To run on the test set:
```bash
python code/translator.py dic/dict.txt corpus/test.txt
```
