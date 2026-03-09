import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = await params;
    
    // Path to images
    const imageDir = path.join(process.cwd(), '..', 'bg-uniform black');

    if (!fs.existsSync(imageDir)) {
      return new NextResponse('Image directory not found', { status: 404 });
    }

    const files = fs.readdirSync(imageDir);
    // Find image that starts with ID and is a png
    // Match either exactly "id.png" or "id_something.png"
    const imageFile = files.find(file => 
      file.toLowerCase() === `${id.toLowerCase()}.png` || 
      file.toLowerCase().startsWith(`${id.toLowerCase()}_`)
    );

    if (!imageFile) {
      return new NextResponse('Image not found', { status: 404 });
    }

    const filePath = path.join(imageDir, imageFile);
    const fileBuffer = fs.readFileSync(filePath);

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error) {
    return new NextResponse('Error reading image', { status: 500 });
  }
}
