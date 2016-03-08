#!/usr/bin/env python

from lxml import etree

from nltk.sentiment.vader import SentimentIntensityAnalyzer

from pattern.en import sentiment

import argh
import math
import time

try:
    import unicornhat as uh
except ImportError:
    pass

LIGHT = 255

TEI_NAMESPACE = 'http://www.tei-c.org/ns/1.0'
NSMAP = {'tei': TEI_NAMESPACE}

UH_LED_COUNT = 64
UH_LED_LINE_COUNT = int(math.sqrt(UH_LED_COUNT))

WORDS_PER_MINUTE = 120


@argh.arg('xml_path', help='Path to a TEI XML file of a play')
@argh.arg('-n', '--nlp', help='The NLP library to use: nltk or pattern')
@argh.arg('-b', '--brightness', help='Brightness for the Unicorn HAT')
@argh.arg('-nu', '--no-unicorns',
          help='Runs the script without using the Unicorn HAT')
@argh.arg('-v', '--verbose',
          help='Prints information about the parsed text: '
          'estimated sentiment, colour intensity, '
          'sleep time after a led is turned on')
def play(xml_path, nlp='nltk',
         brightness=0.2, no_unicorns=False, verbose=False):
    """This script parses a TEI XML encoded play, and applies sentiment
    analysis to each speech. The result of the sentiment analysis is displayed
    on the Unicorn HAT - one pixel per speech - using a range of colours from
    red (negative sentiment) to blue (positive sentiment)."""
    unicorns = not no_unicorns

    if unicorns:
        uh.brightness(brightness)

    lines = _get_lines_from_xml(xml_path)

    for idx, line in enumerate(lines):
        _process_text(idx, line, nlp, unicorns, verbose)


def _process_text(idx, text, nlp, unicorns, verbose):
    polarity = _get_sentiment(text, nlp)
    intensity = int(math.ceil(abs(polarity) * LIGHT))
    r, g, b = _get_colour(polarity, intensity)
    speed = _get_speed(text)

    x = (idx % UH_LED_COUNT) % UH_LED_LINE_COUNT
    y = (idx % UH_LED_COUNT) / UH_LED_LINE_COUNT

    if unicorns:
        _show_pixel(x, y, r, g, b, speed)
    else:
        _print_pixel(x, polarity, speed)

    if verbose:
        print(idx, text, polarity, intensity, speed)


def _get_lines_from_xml(xml_path):
    xml = etree.parse(xml_path)
    sps = xml.xpath('.//tei:sp[tei:speaker]', namespaces=NSMAP)

    lines = []

    for sp in sps:
        text = ' '.join([t.strip() for t in sp.xpath('.//text()')])
        if text:
            lines.append(unicode(text.strip()))

    return lines


def _get_sentiment(text, nlp):
    if nlp == 'pattern':
        return sentiment(text)[0]

    sid = SentimentIntensityAnalyzer()
    return sid.polarity_scores(text)['compound']


def _get_colour(polarity, intensity):
    if polarity == 0.0:
        return 0, 0, 0
    elif polarity > 0.0:
        return LIGHT - intensity, 0, LIGHT
    else:
        return LIGHT, 0, LIGHT - intensity


def _get_speed(text):
    words = text.split()
    count = len(words)
    speed = float(count) / WORDS_PER_MINUTE

    return speed


def _show_pixel(x, y, r, g, b, speed):
    uh.set_pixel(x, y, r, g, b)
    uh.show()
    time.sleep(speed)


def _print_pixel(x, polarity, speed):
    symbol = '.'

    if polarity > 0:
        symbol = '+'
    elif polarity < 0:
        symbol = '-'

    print('{} '.format(symbol)),

    if x == UH_LED_LINE_COUNT - 1:
        print

if __name__ == '__main__':
    argh.dispatch_command(play)
