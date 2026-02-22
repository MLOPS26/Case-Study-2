'use client';

import { useState } from 'react';

export default function Home() {
  const [email, setEmail] = useState('');
  const [userUuid, setUserUuid] = useState('');
  const [question, setQuestion] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [response, setResponse] = useState('');
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'main' | 'history'>('main');

// should throw this somewhere else
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const handleCreateUser = async () => {
    if (!email) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('email', email);
      const res = await fetch(`${BACKEND_URL}/users`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setUserUuid(data.uuid);
    } catch (error) {
      console.error('Error creating user:', error);
    }
    setLoading(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !question || !userUuid) return;

    setLoading(true);
    setResponse('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question', question);
      formData.append('user_uuid', userUuid);

      const res = await fetch(`${BACKEND_URL}/inference`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setResponse(data.response);
      setQuestion('');
      setFile(null);
      setImagePreview(null);
    } catch (error) {
      console.error('Error:', error);
      setResponse('Error processing request');
    }

    setLoading(false);
  };

  const handleLoadHistory = async () => {
    if (!userUuid) return;
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/history/${userUuid}`);
      const data = await res.json();
      setHistory(data);
      setView('history');
    } catch (error) {
      console.error('Error loading history:', error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-white text-black">
      <div className="max-w-2xl mx-auto px-8 py-16">
        <header className="text-center mb-16 border-b-2 border-black pb-8">
          <h1 className="text-6xl font-bold mb-4">¯\_(ツ)_/¯</h1>
          <h2 className="text-2xl font-mono">SHRUG INTELLIGENCE</h2>
          <p className="text-sm mt-2 font-mono">minimal math tutor</p>
        </header>

        {!userUuid && (
          <div className="border-2 border-black p-8 mb-8">
            <h3 className="text-xl font-bold mb-4 font-mono">START</h3>
            <div className="flex gap-4">
              <input
                type="email"
                placeholder="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 border-2 border-black px-4 py-2 font-mono bg-white"
              />
              <button
                onClick={handleCreateUser}
                disabled={loading || !email}
                className="px-6 py-2 bg-black text-white font-mono hover:bg-gray-800 disabled:bg-gray-400"
              >
                {loading ? '...' : 'GO'}
              </button>
            </div>
          </div>
        )}

        {userUuid && view === 'main' && (
          <>
            <div className="mb-4 flex justify-between items-center border-b-2 border-black pb-4">
              <p className="font-mono text-sm">user: {userUuid.substring(0, 8)}...</p>
              <button
                onClick={handleLoadHistory}
                className="px-4 py-1 border-2 border-black font-mono hover:bg-black hover:text-white"
              >
                HISTORY
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="border-2 border-black p-8">
                <label className="block font-mono font-bold mb-4">IMAGE</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="block w-full font-mono text-sm file:mr-4 file:py-2 file:px-4 file:border-2 file:border-black file:bg-white file:font-mono hover:file:bg-black hover:file:text-white"
                />
                {imagePreview && (
                  <div className="mt-4 border-2 border-black p-4">
                    <img src={imagePreview} alt="Preview" className="max-w-full h-auto" />
                  </div>
                )}
              </div>

              <div className="border-2 border-black p-8">
                <label className="block font-mono font-bold mb-4">QUESTION</label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="what is this problem asking?"
                  className="w-full border-2 border-black px-4 py-2 font-mono h-24 bg-white"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !file || !question}
                className="w-full py-4 bg-black text-white font-mono text-xl hover:bg-gray-800 disabled:bg-gray-400"
              >
                {loading ? 'THINKING...' : 'SOLVE'}
              </button>
            </form>

            {response && (
              <div className="mt-8 border-2 border-black p-8">
                <h3 className="font-mono font-bold mb-4">RESPONSE</h3>
                <div className="font-mono whitespace-pre-wrap">{response}</div>
              </div>
            )}
          </>
        )}

        {userUuid && view === 'history' && (
          <>
            <div className="mb-4 flex justify-between items-center border-b-2 border-black pb-4">
              <h3 className="font-mono font-bold text-xl">HISTORY</h3>
              <button
                onClick={() => setView('main')}
                className="px-4 py-1 border-2 border-black font-mono hover:bg-black hover:text-white"
              >
                BACK
              </button>
            </div>

            {history.length === 0 ? (
              <div className="border-2 border-black p-8 text-center font-mono">
                no history yet ¯\_(ツ)_/¯
              </div>
            ) : (
              <div className="space-y-4">
                {history.map((item, idx) => (
                  <div key={idx} className="border-2 border-black p-6">
                    <div className="font-mono text-sm mb-2 opacity-60">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                    {item.image_path && (
                      <div className="mb-4 border-2 border-black p-2">
                        <img
                          src={`${BACKEND_URL}/${item.image_path}`}
                          alt="Question"
                          className="max-w-full h-auto"
                        />
                      </div>
                    )}
                    <div className="mb-2">
                      <span className="font-bold font-mono">Q:</span>
                      <span className="font-mono ml-2">{item.question}</span>
                    </div>
                    <div>
                      <span className="font-bold font-mono">A:</span>
                      <div className="font-mono ml-4 mt-2 whitespace-pre-wrap">
                        {item.response}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
