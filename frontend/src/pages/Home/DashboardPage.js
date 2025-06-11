import React, { useState, useEffect, useCallback } from 'react';
import { User, Image, Calendar, ArrowRight, Loader2, Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const UserDashboard = () => {
  
  const navigate = useNavigate();

  const handleExerciseStart = () => {
    navigate('/routine'); // /exercise 경로로 이동
  };

  const handleDietRecord = () => {
    navigate('/diet'); // /diet 경로로 이동
  };

  const [dashboardData, setDashboardData] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authError, setAuthError] = useState(false); // 인증 에러 상태 추가
  
  // 이미지 업로드 관련 상태
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  
  // 생성 프로세스 관련 상태
  const [generating, setGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStep, setGenerationStep] = useState('');
  const [generationError, setGenerationError] = useState(null);

  // 토큰을 sessionStorage에서 가져오는 함수
  const getAuthToken = () => {
    return sessionStorage.getItem('access_token');
  };

  // 사용자 ID 가져오기
  const getUserId = () => {
    return sessionStorage.getItem('user_id');
  };

  let alertShown = false;

const fetchWithAuth = async (url, options = {}) => {
  const token = getAuthToken();
  const userId = getUserId();
  
  console.log('=== fetchWithAuth 디버깅 ===');
  console.log('저장된 토큰:', token);
  console.log('사용자 ID:', userId);
  console.log('요청 URL:', url);
  
  if (!token) {
    setAuthError(true);
    throw new Error('No authentication token found');
  }
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    ...((!options.method || options.method.toUpperCase() === 'GET') ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  };

  console.log('요청 헤더:', headers);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  console.log('응답 상태:', response.status);
  console.log('응답 헤더:', response.headers);

  if (!response.ok) {
    const errorText = await response.text();
    console.log('에러 응답:', errorText);
    
    if (response.status === 401) {
      console.error('401 에러 발생');
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('user_id');
      sessionStorage.removeItem('token_type');
      setAuthError(true);
      throw new Error('Authentication failed');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};
  // 대시보드 데이터 로드
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const userId = getUserId();
      if (!userId) {
        throw new Error('사용자 ID를 찾을 수 없습니다.');
      }
      
      // 사용자 프로필과 이미지 데이터를 병렬로 가져오기
      const [profile, imageResponse] = await Promise.all([
        fetchWithAuth('http://localhost:8000/api/user/profile'),
        // get_current_img.py의 get_user_image 엔드포인트 사용
        fetchWithAuth(`http://localhost:8000/user/${userId}/image`).catch(() => null)
      ]);
      
      // 대시보드 데이터 구성
      let dashboardData = {
        has_image: false,
        image_data: null,
        content_type: null,
        created_at: null,
        character: null,
        tag: null
      };
      
      // 이미지 응답이 있으면 대시보드 데이터에 설정
      if (imageResponse) {
        dashboardData = {
          has_image: true,
          image_data: imageResponse.image_data, // Base64 인코딩된 이미지 데이터
          content_type: `image/${imageResponse.image_format || 'jpeg'}`,
          created_at: new Date().toISOString(), // 현재 시간으로 설정
          character: imageResponse.character,
          tag: imageResponse.tag
        };
      }
      
      setDashboardData(dashboardData);
      setUserProfile(profile);
      
    } catch (err) {
      setError(err.message);
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // 파일 선택 핸들러
  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setUploadError(null);
      setUploadSuccess(false);
      
      // 미리보기 URL 생성
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setUploadError('이미지 파일만 업로드 가능합니다.');
    }
  };

  // 드래그 앤 드롭 핸들러
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, []);

  // 파일 입력 변경 핸들러
  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  // 이미지 업로드 (생성과 분리)
  const handleUploadImage = async () => {
    if (!selectedFile) {
      setUploadError('파일을 선택해주세요.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const token = getAuthToken();
      const response = await fetch('http://localhost:8000/upload-user-image', {
        method: 'POST',
        headers: {
          // 'Authorization': `Bearer ${token}`,
          'Authorization': 'Bearer ' + token
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('업로드에 실패했습니다.');
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      setUploadSuccess(true);
      
    } catch (err) {
      setUploadError(err.message);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  // 이미지 생성 (업로드와 분리)
  const handleGenerateImages = async () => {
    setGenerating(true);
    setGenerationError(null);
    setGenerationProgress(0);
    setGenerationStep('이미지 생성을 시작합니다...');

    try {
      // 단계별 진행 시뮬레이션
      const steps = [
        '이미지 분석 중...',
        'AI 모델 준비 중...',
        '스타일 생성 중.',
        '스타일 생성 중..',
        '스타일 생성 중...',
        '스타일 생성 중.',
        '스타일 생성 중..',
        '스타일 생성 중...',
        '결과 저장 중...'
      ];

      // 진행 상황 업데이트 시뮬레이션
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          const next = prev + 10;
          if (next < 90) {
            const stepIndex = Math.floor(next / 10);
            if (stepIndex < steps.length) {
              setGenerationStep(steps[stepIndex]);
            }
            return next;
          }
          return prev;
        });
      }, 2000);

      const response = await fetchWithAuth('http://localhost:8000/generate-images', {
        method: 'POST',
        body: JSON.stringify({ base_image_name: "proteengrayal.png" }),
      });

      clearInterval(progressInterval);
      setGenerationProgress(100);
      setGenerationStep('완료!');

      if (response) {
        // 생성 완료 후 대시보드 데이터 새로고침
        setTimeout(() => {
          loadDashboardData();
          setGenerating(false);
          setSelectedFile(null);
          setPreviewUrl(null);
          setUploadSuccess(false);
        }, 1000);
      }

    } catch (err) {
      setGenerationError(err.message);
      setGenerating(false);
      console.error('Generation error:', err);
    }
  };

  // 파일 선택 취소
  const handleClearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadError(null);
    setUploadSuccess(false);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  };

// 3. useEffect 수정 - 토큰 검증 로직 개선
useEffect(() => {
  const token = getAuthToken();
  const userId = getUserId();

  console.log("Dashboard useEffect 실행");
  console.log("access_token:", token);
  console.log("user_id:", userId);

  if (!token || !userId) {
    console.warn('인증 정보 없음. 로그인으로 이동');
    setAuthError(true);
    setTimeout(() => {
      navigate('/login');
    }, 1000);
    return;
  }

  // 인증 정보가 명확히 존재하는 경우에만 load
  loadDashboardData();
}, []);

  // 컴포넌트 언마운트 시 URL 정리
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // 이미지 생성 페이지로 이동
  const handleGoToGeneration = () => {
    console.log('이미지 생성 페이지로 이동');
    alert('이미지 생성 페이지로 이동합니다.');
  };

  // 갤러리 페이지로 이동
  const handleGoToGallery = () => {
    console.log('갤러리 페이지로 이동');
    alert('갤러리 페이지로 이동합니다.');
  };

  // 로그아웃 함수
  const handleLogout = () => {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_id');
    alert('로그아웃되었습니다.');
    console.log('로그아웃');
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
          <p className="text-gray-600">대시보드를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">오류가 발생했습니다</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={loadDashboardData}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

if (authError) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg text-center max-w-md">
        <div className="text-red-500 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">인증이 필요합니다</h2>
        <p className="text-gray-600 mb-4">로그인 페이지로 이동합니다...</p>
        <div className="flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-purple-600" />
        </div>
      </div>
    </div>
  );
}

  // 1. 전체 배경을 회색으로 변경
return (
  <div className="min-h-screen bg-gray-100">
    {/* 상단 버튼들 추가 */}
    <div className="pt-8 pb-4">
      <div className="max-w-4xl mx-auto px-4 flex justify-center gap-4">
        <button 
          onClick={handleExerciseStart}
          className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-full font-medium transition-colors shadow-lg"
        >
          운동 시작하기
        </button>
        <button 
          onClick={handleDietRecord}
          className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-full font-medium transition-colors shadow-lg"
        >
          식단 기록하기
        </button>
      </div>
    </div>

    {/* 메인 컨텐츠 - 중앙 파란 원 */}
    <main className="max-w-4xl mx-auto px-4">
      <div className="flex justify-center items-center" style={{ minHeight: '60vh' }}>
        {dashboardData?.has_image ? (
          // 이미지가 있는 경우 - 파란 원 안에 이미지 표시
          <div className="relative">
            <div className="w-80 h-80 bg-blue-400 flex items-center justify-center shadow-lg rounded-full">
              <img
                src={`data:${dashboardData.content_type};base64,${dashboardData.image_data}`}
                alt={`AI 생성 아바타 (${dashboardData.tag || 'Unknown'} 스타일)`}
                className="w-72 h-72 object-cover rounded-full"
              />
            </div>
            {/* 스타일 태그 */}
            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
              <span className="inline-block bg-purple-100 text-purple-800 text-sm px-3 py-1 rounded-full">
                {dashboardData.tag || 'Unknown'} 스타일
              </span>
            </div>
          </div>
        ) : (
          // 이미지가 없는 경우 - 빈 파란 원과 업로드 인터페이스
          <div className="text-center">
            {!generating ? (
              <div className="space-y-8">
                {/* 파란 원 영역 */}
                <div className="relative">
                  <div 
                    className={`w-80 h-80 bg-blue-400 rounded-full flex items-center justify-center transition-all duration-300 ${
                      dragActive ? 'bg-blue-500 scale-105' : ''
                    } ${previewUrl ? 'overflow-hidden' : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    {previewUrl ? (
                      // 미리보기 이미지
                      <div className="relative w-full h-full">
                        <img
                          src={previewUrl}
                          alt="미리보기"
                          className="w-full h-full object-cover rounded-full"
                        />
                        <button
                          onClick={handleClearFile}
                          className="absolute top-4 right-4 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition-colors shadow-lg"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      // 업로드 인터페이스
                      <div className="text-center text-white">
                        <Upload className="h-16 w-16 mx-auto mb-4 opacity-80" />
                        <p className="text-lg font-medium mb-2">
                          이미지를 드래그하여<br />업로드하세요
                        </p>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleFileInputChange}
                          className="hidden"
                          id="file-input"
                        />
                        <label
                          htmlFor="file-input"
                          className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-full cursor-pointer transition-all inline-block"
                        >
                          파일 선택
                        </label>
                      </div>
                    )}
                  </div>
                </div>

                {/* 에러 메시지 */}
                {uploadError && (
                  <div className="max-w-md mx-auto p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                    <span className="text-red-700 text-sm">{uploadError}</span>
                  </div>
                )}

                {/* 성공 메시지 */}
                {uploadSuccess && (
                  <div className="max-w-md mx-auto p-3 bg-green-50 border border-green-200 rounded-lg flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    <span className="text-green-700 font-medium">업로드 완료!</span>
                  </div>
                )}

                {/* 액션 버튼들 */}
                <div className="flex flex-col gap-4 items-center">
                  {selectedFile && !uploadSuccess && (
                    <button
                      onClick={handleUploadImage}
                      disabled={uploading}
                      className="bg-blue-600 text-white px-8 py-3 rounded-full hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center font-medium"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin mr-2" />
                          업로드 중...
                        </>
                      ) : (
                        "이미지 업로드"
                      )}
                    </button>
                  )}

                  {uploadSuccess && (
                    <button
                      onClick={handleGenerateImages}
                      disabled={generating}
                      className="bg-purple-600 text-white px-8 py-3 rounded-full hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center text-lg font-medium shadow-lg"
                    >
                      AI 이미지 생성 시작
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </button>
                  )}
                </div>
              </div>
            ) : (
              // 생성 중 상태 - 파란 원 안에 로딩
              <div className="space-y-6">
                <div className="w-80 h-80 bg-blue-400 rounded-full flex flex-col items-center justify-center text-white">
                  <Loader2 className="h-16 w-16 animate-spin mb-4" />
                  <h3 className="text-xl font-semibold mb-2">생성 중...</h3>
                  <p className="text-sm opacity-90 text-center px-4">{generationStep}</p>
                  
                  {/* 진행률 바 - 원 안에 */}
                  <div className="w-48 bg-white bg-opacity-20 rounded-full h-2 mt-4">
                    <div
                      className="bg-white h-2 rounded-full transition-all duration-500"
                      style={{ width: `${generationProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs mt-2 opacity-75">{generationProgress}% 완료</p>
                </div>
                
                {generationError && (
                  <div className="max-w-md mx-auto p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
                    <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
                    <span className="text-red-700 text-sm">{generationError}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  </div>
);
};

export default UserDashboard;