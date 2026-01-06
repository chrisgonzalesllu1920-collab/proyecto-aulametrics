import streamlit as st
import os
import pandas as pd
import io
import re 
import random
import string
import json
from google import genai
from google.genai.errors import APIError 
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.text.paragraph import Paragraph
from docx.table import _Cell
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


