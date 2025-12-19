import { useState, useRef, ChangeEvent, FormEvent } from 'react';
import { Upload as UploadIcon, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { supabase } from '../lib/supabase';

export default function Upload({ onNavigate }: { onNavigate: (page: string, projectId?: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    setError('');
    setSuccess(false);

    if (selectedFile) {
      const fileExtension = selectedFile.name.split('.').pop()?.toLowerCase();
      if (fileExtension !== 'dwg' && fileExtension !== 'dxf') {
        setError('Please upload a valid .dwg or .dxf file');
        setFile(null);
        return;
      }

      if (selectedFile.size > 50 * 1024 * 1024) {
        setError('File size must be less than 50MB');
        setFile(null);
        return;
      }

      setFile(selectedFile);
      if (!projectName) {
        setProjectName(selectedFile.name.replace(/\.(dwg|dxf)$/i, ''));
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];

    if (droppedFile) {
      const fileExtension = droppedFile.name.split('.').pop()?.toLowerCase();
      if (fileExtension !== 'dwg' && fileExtension !== 'dxf') {
        setError('Please upload a valid .dwg or .dxf file');
        return;
      }

      if (droppedFile.size > 50 * 1024 * 1024) {
        setError('File size must be less than 50MB');
        return;
      }

      setFile(droppedFile);
      if (!projectName) {
        setProjectName(droppedFile.name.replace(/\.(dwg|dxf)$/i, ''));
      }
      setError('');
      setSuccess(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const removeFile = () => {
    setFile(null);
    setError('');
    setSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const simulateProcessing = async () => {
    for (let i = 0; i <= 100; i += 10) {
      setUploadProgress(i);
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    if (!projectName.trim()) {
      setError('Please enter a project name');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      await simulateProcessing();

      const fileType = file.name.split('.').pop()?.toLowerCase() || '';
      const totalFixtures = Math.floor(Math.random() * 50) + 10;
      const avgCostPerFixture = 35.50;
      const totalCost = totalFixtures * avgCostPerFixture;
      const avgLux = Math.floor(Math.random() * 200) + 300;

      const { data: projectData, error: projectError } = await supabase
        .from('projects')
        .insert({
          name: projectName,
          file_name: file.name,
          file_type: fileType,
          total_fixtures: totalFixtures,
          total_cost: totalCost,
          average_lux: avgLux,
          user_id: '00000000-0000-0000-0000-000000000000',
        })
        .select()
        .single();

      if (projectError) throw projectError;

      const { data: models, error: modelsError } = await supabase
        .from('fixture_models')
        .select('*')
        .limit(5);

      if (modelsError) throw modelsError;

      if (projectData && models) {
        const rooms = ['Office 1', 'Conference Room', 'Lobby', 'Hallway', 'Workshop'];
        const symbols = ['LIGHT_01', 'LIGHT_02', 'LIGHT_03', 'DOWNLIGHT', 'PANEL_600'];

        const fixturesData = [];
        for (let i = 0; i < Math.min(totalFixtures, 15); i++) {
          const randomModel = models[Math.floor(Math.random() * models.length)];
          fixturesData.push({
            project_id: projectData.id,
            room_name: rooms[Math.floor(Math.random() * rooms.length)],
            detected_symbol: symbols[Math.floor(Math.random() * symbols.length)],
            selected_model_id: randomModel.id,
            quantity: Math.floor(Math.random() * 5) + 1,
            lux_level: Math.floor(Math.random() * 200) + 300,
          });
        }

        const { error: fixturesError } = await supabase
          .from('fixtures')
          .insert(fixturesData);

        if (fixturesError) throw fixturesError;

        setSuccess(true);
        setTimeout(() => {
          onNavigate('results', projectData.id);
        }, 1500);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload and process file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Upload CAD File</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Upload your .dwg or .dxf file to analyze lighting fixtures
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Project Name
          </label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Enter project name"
            disabled={uploading}
          />
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
            CAD File Upload
          </label>

          {!file ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                <span className="font-semibold text-blue-600 dark:text-blue-400">Click to upload</span> or drag and drop
              </p>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                .DWG or .DXF files up to 50MB
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".dwg,.dxf"
                onChange={handleFileChange}
                className="hidden"
                disabled={uploading}
              />
            </div>
          ) : (
            <div className="border border-gray-300 dark:border-gray-600 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <File className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{file.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              {!uploading && (
                <button
                  type="button"
                  onClick={removeFile}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              )}
            </div>
          )}

          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          {success && (
            <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700 dark:text-green-400">
                File uploaded successfully! Redirecting to results...
              </p>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => onNavigate('dashboard')}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            disabled={uploading}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!file || uploading}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md transition-colors flex items-center space-x-2"
          >
            <UploadIcon className="w-5 h-5" />
            <span>{uploading ? 'Processing...' : 'Upload & Analyze'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
