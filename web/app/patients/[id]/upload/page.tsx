"use client";
import { useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { panelsApi } from "@/lib/api";
import Sidebar from "@/components/Sidebar";

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [drawnAt, setDrawnAt] = useState(new Date().toISOString().split("T")[0]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f?.type === "application/pdf" || f?.name.endsWith(".pdf")) {
      setFile(f);
      setError("");
    } else {
      setError("Please drop a PDF file.");
    }
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const res = await panelsApi.uploadPdf(id, file, drawnAt + "T00:00:00Z");
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  if (result) {
    return (
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="max-w-2xl mx-auto px-6 py-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-lg">✓</span>
                </div>
                <h2 className="text-lg font-semibold text-gray-900">Lab Report Imported</h2>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                  <div className="text-gray-400 text-xs mb-0.5">Lab</div>
                  <div className="font-medium text-gray-900">{result.lab_name || "Unknown Lab"}</div>
                </div>
                <div>
                  <div className="text-gray-400 text-xs mb-0.5">Parse Confidence</div>
                  <div className={`font-medium ${
                    result.parse_confidence >= 0.7 ? "text-green-600" :
                    result.parse_confidence >= 0.4 ? "text-yellow-600" : "text-red-600"
                  }`}>
                    {Math.round(result.parse_confidence * 100)}%
                  </div>
                </div>
                <div>
                  <div className="text-gray-400 text-xs mb-0.5">Markers Extracted</div>
                  <div className="font-medium text-gray-900">{result.total_markers_found}</div>
                </div>
                <div>
                  <div className="text-gray-400 text-xs mb-0.5">PhenoAge Markers</div>
                  <div className="font-medium text-gray-900">
                    {result.phenoage_markers_found?.length || 0}/9
                  </div>
                </div>
              </div>

              {result.phenoage_markers_found?.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs text-gray-400 mb-1">PhenoAge markers found:</div>
                  <div className="flex flex-wrap gap-1">
                    {result.phenoage_markers_found.map((m: string) => (
                      <span key={m} className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted values preview */}
              <div className="border border-gray-100 rounded-lg overflow-hidden mb-4">
                <div className="px-3 py-2 bg-gray-50 text-xs font-medium text-gray-500 border-b border-gray-100">
                  Extracted Values
                </div>
                <div className="max-h-48 overflow-y-auto">
                  {result.values?.map((v: any) => (
                    <div key={v.marker_key} className="flex justify-between px-3 py-1.5 text-sm border-b border-gray-50 last:border-0">
                      <span className="text-gray-600">{v.marker_display || v.marker_key}</span>
                      <span className={`font-medium ${
                        v.flag === "H" ? "text-red-600" : v.flag === "L" ? "text-yellow-600" : "text-gray-900"
                      }`}>
                        {v.value} {v.unit}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <Link
                  href={`/patients/${id}`}
                  className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
                >
                  View Patient →
                </Link>
                <button
                  onClick={() => { setResult(null); setFile(null); }}
                  className="px-5 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  Upload Another
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto px-6 py-8">
          <div className="flex items-center gap-2 mb-6 text-sm">
            <Link href={`/patients/${id}`} className="text-gray-400 hover:text-gray-600">
              ← Patient
            </Link>
            <span className="text-gray-300">/</span>
            <span className="text-gray-600">Upload Labs</span>
          </div>

          <h1 className="text-2xl font-semibold text-gray-900 mb-2">Upload Lab Report</h1>
          <p className="text-sm text-gray-500 mb-6">
            Upload a PDF from Quest Diagnostics, LabCorp, or any standard lab format.
            Biomarkers are extracted automatically.
          </p>

          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
            {/* Drop zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                dragging ? "border-green-400 bg-green-50" :
                file ? "border-green-300 bg-green-50/50" :
                "border-gray-200 hover:border-gray-300"
              }`}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) { setFile(f); setError(""); }
                }}
              />
              {file ? (
                <div>
                  <div className="text-2xl mb-2">📄</div>
                  <div className="font-medium text-gray-900 text-sm">{file.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {(file.size / 1024).toFixed(0)} KB
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="text-xs text-red-500 hover:text-red-700 mt-2"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div>
                  <div className="text-3xl mb-2">📋</div>
                  <div className="text-sm font-medium text-gray-700">Drop PDF here or click to browse</div>
                  <div className="text-xs text-gray-400 mt-1">Quest, LabCorp, or any standard lab PDF</div>
                </div>
              )}
            </div>

            {/* Draw date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Draw Date</label>
              <input
                type="date"
                value={drawnAt}
                onChange={(e) => setDrawnAt(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-700">
              <strong>Supported markers:</strong> Albumin, Creatinine, Glucose, ALP, WBC, Lymphocytes, MCV, RDW, hsCRP, LDL, HDL, Triglycerides, HbA1c, Testosterone, TSH, Ferritin, Vitamin D, Homocysteine, eGFR, and 40+ more.
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
            >
              {uploading ? "Parsing PDF..." : "Import Lab Report"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
