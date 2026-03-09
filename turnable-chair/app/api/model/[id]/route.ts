import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = await params;
  
  // Base path to NM_stolar relative to project root
  // Assuming the API is running from within turnable-chair/
  // The structure is:
  // /stolar-db/turnable-chair/app/api/model/[id]/route.ts
  // /stolar-db/NM_stolar/[id]/
  const modelDir = path.join(process.cwd(), '..', 'NM_stolar', id);

  if (!fs.existsSync(modelDir)) {
    return new NextResponse('Model directory not found', { status: 404 });
  }

  try {
    const files = fs.readdirSync(modelDir);
    const glbFile = files.find(file => file.endsWith('.glb'));

    if (!glbFile) {
      return new NextResponse('GLB file not found', { status: 404 });
    }

    const filePath = path.join(modelDir, glbFile);
    const fileBuffer = fs.readFileSync(filePath);

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'model/gltf-binary',
        'Content-Disposition': `attachment; filename="${glbFile}"`,
      },
    });
  } catch (error) {
    return new NextResponse('Error reading model', { status: 500 });
  }
}
