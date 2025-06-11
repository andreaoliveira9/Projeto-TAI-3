//
// Armando J. Pinho, ap@ua.pt, 2016-2020
//
// See:
// http://www.mega-nerd.com/libsndfile
// http://www.fftw.org
//
// In linux, compile with:
// g++ -W -Wall -std=c++11 -o GetMaxFreqs GetMaxFreqs.cpp -lsndfile -lfftw3 -lm
//
// It should accept .wav and .flac audio files, stereo, sampled at 44100 Hz, 16 bits
//
// Example:
// GetMaxFreqs -w test.freqs test.wav
//
// File test.freqs will contain the "signature" of the audio file test.wav
//
#include <iostream>
#include <fstream>
#include <cstdio>
#include <cstring> // Required for memset
#include <algorithm>
#include <sndfile.hh>
#include <fftw3.h>

#define WS  1024  // Size of the window for computing the FFT
#define SH  256   // Window overlap
#define DS  4   // Down-sampling factor
#define NF  4   // Number of significant frequencies

using namespace std;

int main (int argc, char* argv[]) {

  bool verbose { false };
  char* oFName = nullptr;
  ofstream os;
  int ws_val { WS }; // Changed variable name to avoid conflict with macro
  int sh { SH };
  int ds { DS };
  int nf { NF };

  if(argc < 2) {
    cerr << "Usage: GetMaxFreqs [ -v (verbose) ]" << endl;
    cerr << "                   [ -w freqsFile ]" << endl;
    cerr << "                   [ -ws winSize ]" << endl;
    cerr << "                   [ -sh shift ]" << endl;
    cerr << "                   [ -ds downSampling ]" << endl;
    cerr << "                   [ -nf nFreqs ]" << endl;
    cerr << "                   AudioFile" << endl;
    return 1;
  }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-v") {
      verbose = true;
      break;
    }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-w") {
      oFName = argv[n+1];
      break;
    }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-ws") {
      ws_val = atoi(argv[n+1]); // Use ws_val
      break;
    }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-sh") {
      sh = atoi(argv[n+1]);
      break;
    }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-ds") {
      ds = atoi(argv[n+1]);
      break;
    }

  for(int n = 1 ; n < argc ; n++)
    if(string(argv[n]) == "-nf") {
      nf = atoi(argv[n+1]);
      break;
    }

  SndfileHandle audioFile { argv[argc-1] };
  if(audioFile.error()) {
    cerr << "Error: invalid audio file\n";
    return 1;
  }

  if(audioFile.channels() != 2) {
    cerr << "Error: currently supports only 2 channels\n";
    return 1;
  }

  if(audioFile.samplerate() != 44100) {
    cerr << "Error: currently supports only 44100 Hz of sample rate\n";
    return 1;
  }

  if(verbose) {
    printf("Sample rate : %d\n",  audioFile.samplerate());
    printf("Channels    : %d\n",  audioFile.channels());
    printf("Frames      : %ld\n", (long int)audioFile.frames());
  }

  if(oFName != nullptr) {
    os.open(oFName, ofstream::binary);
    if(!os) {
      cerr << "Warning: failed to open file to write\n";
    }

  }

  short* samples = new short[audioFile.frames() << 1];
  audioFile.readf(samples, audioFile.frames());

  // --- START OF CHANGES ---
  // Allocate fftw_complex arrays dynamically instead of using VLAs
  fftw_complex* in = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * ws_val);
  fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * ws_val);

  // Check if allocation was successful
  if (!in || !out) {
      cerr << "Error: Failed to allocate memory for FFT arrays." << endl;
      delete[] samples;
      return 1;
  }

  // Manually zero-initialize 'in' as fftw_complex in[ws] = {} would have done
  memset(in, 0, sizeof(fftw_complex) * ws_val);

  fftw_plan plan;
  double power[ws_val/2]; // ws_val is known at this point, so it's a VLA here.
                          // It's technically still a VLA, but uninitialized VLAs
                          // are often allowed by GCC/Clang as an extension, unlike
                          // initialized ones. For strict C++11, std::vector
                          // would be ideal here too.

  plan = fftw_plan_dft_1d(ws_val, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
  // --- END OF CHANGES ---

  for(int n = 0 ; n <= (audioFile.frames() - ws_val * ds) / (sh * ds) ; ++n) {
    for(int k = 0 ; k < ws_val ; ++k) { // Convert to mono and down-sample
      in[k][0] = (int)samples[(n * (sh * ds) + k * ds) << 1] +
        samples[((n * (sh * ds) + k * ds) << 1) + 1];
      for(int l = 1 ; l < ds ; ++l) {
        in[k][0] += (int)samples[(n * (sh * ds) + k * ds + l) << 1] +
          samples[((n * (sh * ds) + k * ds + l) << 1) + 1];
      }

    }

    fftw_execute(plan);

    for(int k = 0 ; k < ws_val/2 ; ++k)
      power[k] = out[k][0] * out[k][0] + out[k][1] * out[k][1];

    // --- Potential VLA here if ws_val/2 is not constant ---
    // If you need to strictly avoid VLAs, even uninitialized ones,
    // this line would also need to become dynamic allocation:
    // unsigned* maxPowerIdx = new unsigned[ws_val/2];
    // And then delete[] maxPowerIdx at the end of the loop iteration
    // or after the loop if its scope allows.
    unsigned maxPowerIdx[ws_val/2];
    for(int k = 0 ; k < ws_val/2 ; ++k)
      maxPowerIdx[k] = k;

    partial_sort(maxPowerIdx, maxPowerIdx + nf, maxPowerIdx + ws_val/2,
      [&power](int i, int j) { return power[i] > power[j]; });

    if(os) {
      for(int i = 0 ; i < nf ; ++i) {
        // To store in a byte, truncate to a max of 255
        os.put(maxPowerIdx[i] > 255 ? 255 : maxPowerIdx[i]);
      }

    }

  }

  delete[] samples;
  fftw_destroy_plan(plan);
  // --- START OF NEW CLEANUP ---
  fftw_free(in);  // Use fftw_free for memory allocated with fftw_malloc
  fftw_free(out); // Use fftw_free for memory allocated with fftw_malloc
  // --- END OF NEW CLEANUP ---

  return 0 ;
}