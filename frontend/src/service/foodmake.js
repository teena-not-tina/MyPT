export async function generateFoodImage(foodName) {
  const response = await fetch('http://localhost:5000/generate-food', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ food: foodName })
  });
  if (!response.ok) throw new Error('API 오류');
  const data = await response.json();
  return data.image_base64;
}