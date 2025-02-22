import logging
from xQuiz.quiz_handler import QuizHandler
from config import QUIZ_TOPIC_ID

logger = logging.getLogger(__name__)

def start_quiz():
    """
    Rozpoczyna quiz, generując pierwsze pytanie i publikując je na forum.
    """
    quiz_handler = QuizHandler()
    content = "start quiz"  # Treść inicjująca rozpoczęcie quizu
    quiz_handler.handle_quiz_topic_create(QUIZ_TOPIC_ID, content)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_quiz()