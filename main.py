# [1차]: Mini Redis 실행 진입점(Main Entry Point) 모듈을 정의합니다.
# [2차]: Mini Redis 매장 건물의 정문 출입문입니다.
"""
Mini Redis 실행 진입점 (Entry Point)
"""

# [1차]: cli 모듈로부터 run_cli 함수를 임포트합니다.
# [2차]: 카운터 매니저를 출입문 앞으로 부릅니다.
from src.cli import run_cli

# [1차]: 이 스크립트가 파이썬 인터프리터에서 직접 실행되었는지 확인합니다 (__name__ == '__main__').
# [2차]: 손님이 정문 문고리를 직접 잡고 열었을 때만 매장을 개장합니다.
if __name__ == "__main__":
    # [1차]: CLI REPL 대화형 세션을 실행합니다.
    # [2차]: 카운터를 활짝 열고 영업을 시작합니다!
    run_cli()
