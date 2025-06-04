# create_mypt_react_structure.py

import os
import shutil

# React 프로젝트의 src 폴더 경로
# 이 스크립트를 mypt-frontend 프로젝트의 루트 디렉토리에 저장했다고 가정
PROJECT_ROOT = os.getcwd()
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# 11.png 이미지에 기반한 생성할 폴더 및 파일 구조 정의
# 'folder': 폴더를 나타냄
# 'file': 빈 JS 파일을 나타냄 (자동으로 .js 확장자 붙임)
# 'css_file': 빈 CSS 파일을 나타냄 (자동으로 .css 확장자 붙임)
STRUCTURE = {
    'components': {
        'Auth': {
            'LoginForm.js': 'file', # 파일 내용은 수동으로 채워야 함
            'SignupForm.js': 'file', # 파일 내용은 수동으로 채워야 함
        },
        'Chatbot': {
            'MessageBubble.js': 'file',
            'ChatInput.js': 'file',
        },
        # 이미지에 'MainPage' 컴포넌트가 있지만, 'pages/Home/DashboardPage.js'가 메인 역할을 하므로 제외했습니다.
        # 만약 별도의 메인 레이아웃 컴포넌트가 필요하다면 'Shared/Layout.js' 등으로 추가하는 것을 권장합니다.
        # 'MainPage': 'folder', 
        'Exercise': 'folder', # ExerciseDetail.js, ExerciseCard.js 등 추가 예정
        'Diet': 'folder',     # DietItem.js 등 추가 예정
        'Shared': { # 공통 컴포넌트 폴더 (제가 제안한 구조)
            'Header.js': 'file',
            'Header.css': 'css_file',
            'Navbar.js': 'file',
            'Navbar.css': 'css_file',
            # 'Button.js': 'file', # 예시
            # 'Button.css': 'css_file', # 예시
        }
    },
    'pages': {
        'Auth': {
            'LoginPage.js': 'file', # 파일 내용은 수동으로 채워야 함
            'SignupPage.js': 'file', # 파일 내용은 수동으로 채워야 함
        },
        'Onboarding': {
            'InbodyFormPage.js': 'file',
        },
        'Home': {
            'DashboardPage.js': 'file', # 메인 홈 대시보드
        },
        'Routine': {
            'RoutineOverviewPage.js': 'file',
            'RoutineDetailPage.js': 'file',
            'ExerciseCameraPage.js': 'file',
        },
        'Diet': {
            'IngredientInputPage.js': 'file',
            'MenuRecommendationPage.js': 'file',
        },
        'AI': {
            'ChatbotPage.js': 'file',
            'ChatbotPage.css': 'css_file', # ChatbotPage는 별도 CSS를 가짐
            'AvatarProgressPage.js': 'file',
        },
        'NotFoundPage.js': 'file',
    },
    'services': {
        'api.js': 'file',
        'authService.js': 'file',
        'userService.js': 'file',
        'routineService.js': 'file',
        'dietService.js': 'file',
        'aiService.js': 'file',
    },
    'stores': { # 상태 관리를 위한 폴더 (Zustand 등)
        'authStore.js': 'file',
        'userStore.js': 'file',
        # ... 기타 필요한 스토어
    },
    'assets': { # 이미지, 아이콘, 폰트 등
        'images': 'folder',
        'icons': 'folder',
        # 'fonts': 'folder',
    },
    'styles': { # 전역 및 공통 스타일
        'global.css': 'css_file',
        # 'variables.css': 'css_file',
    },
    'hooks': { # 사용자 정의 훅스
        'useAuth.js': 'file',
        # 'useFormValidation.js': 'file',
    },
    'utils': { # 유틸리티 함수
        'validation.js': 'file',
        'helpers.js': 'file',
    }
}

# create-react-app이 기본적으로 생성하는 삭제할 파일 목록 (src 폴더 기준)
FILES_TO_DELETE = [
    'App.css',
    'index.css',
    'logo.svg',
    'reportWebVitals.js',
    'setupTests.js',
    # 'App.test.js' # 테스트 파일을 사용하지 않을 경우 삭제
]

def create_structure(base_path, structure):
    for name, item_type in structure.items():
        full_path = os.path.join(base_path, name)

        if isinstance(item_type, dict): # 폴더 안에 하위 폴더/파일이 있는 경우
            os.makedirs(full_path, exist_ok=True)
            print(f"Created folder: {full_path}")
            create_structure(full_path, item_type) # 재귀 호출
        elif item_type == 'folder': # 빈 폴더
            os.makedirs(full_path, exist_ok=True)
            print(f"Created folder: {full_path}")
        elif item_type == 'file': # .js 파일 생성
            file_name = name if name.endswith('.js') else f"{name}.js"
            file_path = os.path.join(base_path, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass # 빈 파일 생성
                print(f"Created file: {file_path}")
        elif item_type == 'css_file': # .css 파일 생성
            file_name = name if name.endswith('.css') else f"{name}.css"
            file_path = os.path.join(base_path, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass # 빈 파일 생성
                print(f"Created CSS file: {file_path}")
        # 'js_file', 'placeholder' 타입은 'file'과 'css_file'로 일반화했으므로 제거

def delete_unnecessary_files(src_dir, files_to_delete):
    print("\nAttempting to delete unnecessary files from src/ folder:")
    for file_name in files_to_delete:
        file_path = os.path.join(src_dir, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")
        else:
            print(f"File not found, skipping: {file_path}")

if __name__ == "__main__":
    print(f"Starting to create React project structure in: {SRC_DIR}")
    create_structure(SRC_DIR, STRUCTURE)
    print("Structure creation complete.")

    delete_unnecessary_files(SRC_DIR, FILES_TO_DELETE)
    print("\nCleanup complete. Please manually review the 'src' folder and fill file contents.")
    print("Remember to update App.js and index.js with the provided code snippets.")