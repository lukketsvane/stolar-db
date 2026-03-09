import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = await params;
    
    // Base path to NM_stolar relative to project root
    const modelDir = path.join(process.cwd(), '..', 'NM_stolar', id);

    if (!fs.existsSync(modelDir)) {
      return new NextResponse('Model directory not found', { status: 404 });
    }

    const files = fs.readdirSync(modelDir);
    const glbFile = files.find(file => file.endsWith('.glb'));

    if (!glbFile) {
      return new NextResponse('GLB file not found', { status: 404 });
    }

    const filePath = path.join(modelDir, glbFile);
    
    // Using stream for better handling of large binary files
    const fileStream = fs.createReadStream(filePath);
    
    // Convert ReadStream to ReadableStream for NextResponse
    const stream = new ReadableStream({
      start(controller) {
        fileStream.on('data', (chunk) => controller.enqueue(chunk));
        fileStream.on('end', () => controller.close());
        fileStream.on('error', (err) => controller.error(err));
      }
    });

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'model/gltf-binary',
        'Content-Disposition': `attachment; filename="${glbFile}"`,
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error) {
    console.error('[API] Error serving model:', error);
    return new NextResponse('Error reading model', { status: 500 });
  }
}
