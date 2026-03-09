import { put } from '@vercel/blob';
import fs from 'fs';
import path from 'path';

const BLOB_READ_WRITE_TOKEN = "vercel_blob_rw_nu146j3JmwmJgdvV_rJmcpU5sihy76eq2BCmfTWhfG5VegP";

async function uploadImages() {
  const imageDir = path.join(process.cwd(), 'public', 'bg-uniform white');
  if (!fs.existsSync(imageDir)) {
    console.error("Image directory not found!");
    return;
  }

  const files = fs.readdirSync(imageDir).filter(f => f.endsWith('.png'));
  console.log(`Lastar opp ${files.length} bilete til Vercel Blob... Dette kan ta litt tid.`);

  for (const file of files) {
    const filePath = path.join(imageDir, file);
    const fileBuffer = fs.readFileSync(filePath);
    
    try {
      const blob = await put(`images/${file}`, fileBuffer, {
        access: 'public',
        token: BLOB_READ_WRITE_TOKEN,
        contentType: 'image/png'
      });
      console.log(`Lasta opp: ${file} -> ${blob.url}`);
    } catch (error) {
      console.error(`Feil ved opplasting av ${file}:`, error);
    }
  }
  
  console.log("Alle bilete er lasta opp!");
}

uploadImages();
