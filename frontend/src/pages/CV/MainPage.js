import React, { useState } from 'react';
import { analyzeImage } from '../../service/api.js';
import { Upload, Image, FileText, Brain, Loader2 } from 'lucide-react';


const MainPage = () => {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const handleChange = (e) => {
    const file = e.target.files[0];
    setImage(file);
    
    // 이미지 미리보기 생성
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }
  };

  const handleSubmit = async () => {
    if (!image) return;
    setLoading(true);
    try {
      const result = await analyzeImage(image);
      setResults(result);
    } catch (error) {
      console.error('분석 중 오류 발생:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setImage(null);
    setResults(null);
    setPreview(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* 헤더 */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              AI 이미지 분석기
            </h1>
            <p className="text-gray-600">
              이미지를 업로드하여 객체 탐지, OCR, AI 분석을 받아보세요
            </p>
          </div>

          {/* 메인 카드 */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* 파일 업로드 영역 */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-gray-700 mb-4">
                이미지 업로드
              </label>
              
              <div className="relative">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-600">
                    클릭하거나 파일을 드래그하여 업로드하세요
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    JPG, PNG, GIF 파일 지원
                  </p>
                </div>
              </div>

              {/* 이미지 미리보기 */}
              {preview && (
                <div className="mt-6">
                  <img
                    src={preview}
                    alt="미리보기"
                    className="max-w-full h-64 object-contain mx-auto rounded-lg border"
                  />
                  <div className="flex justify-center gap-4 mt-4">
                    <button
                      onClick={handleSubmit}
                      disabled={loading}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          분석 중...
                        </>
                      ) : (
                        <>
                          <Brain className="h-4 w-4" />
                          분석 시작
                        </>
                      )}
                    </button>
                    <button
                      onClick={resetForm}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                    >
                      초기화
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* 결과 표시 영역 */}
            {results && (
              <div className="border-t pt-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                  <Image className="h-6 w-6" />
                  분석 결과
                </h2>

                <div className="grid md:grid-cols-3 gap-6">
                  {/* 객체 탐지 결과 */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      탐지된 객체
                    </h3>
                    <div className="space-y-3">
                      {results.detections.map((d, i) => (
                        <div key={i} className="flex justify-between items-center">
                          <span className="text-gray-700 font-medium">{d.class}</span>
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${d.confidence * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-600 min-w-fit">
                              {(d.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* OCR 결과 */}
                  <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-600" />
                      OCR 텍스트
                    </h3>
                    <div className="bg-white rounded-lg p-4 border">
                      <p className="text-gray-700 leading-relaxed">
                        {results.ocr_text || '텍스트가 감지되지 않았습니다.'}
                      </p>
                    </div>
                  </div>

                  {/* AI 분석 결과 */}
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <Brain className="h-5 w-5 text-purple-600" />
                      AI 추론
                    </h3>
                    <div className="bg-white rounded-lg p-4 border">
                      <p className="text-gray-700 leading-relaxed">
                        {results.gemini_result}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainPage;