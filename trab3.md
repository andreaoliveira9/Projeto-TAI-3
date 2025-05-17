# Universidade de Aveiro

### Departamento de Electr ́onica, Telecomunicac ̧oes e Inform ̃ ́atica

## Algorithmic Information Theory (2024/25)

## Lab work n◦3 — Due: 13 Jun 2025 (to present on 16 Jun 2025)

## Information distances

The Normalized Compression Distance (NCD) is an approximation, using compression, of the
non-computable Normalized Information Distance (NID), defined as

```
NID(x, y) =maxmax{K{K(x(|yx)), K, K((yy|)x})},
```
whereK(x) is the Kolmogorov complexity of string xandK(x|y) is the Kolmogorov com-
plexity ofxwhenyis given as additional information. To avoid the non-computability of the
Kolmogorov complexity, the NCD uses the approximation

```
NCD(x, y) =C(x, ymax)−{minC(x{)C, C(x(y), C)}(y)},
```
whereC(x) denotes the number of bits required by compressorCto representxandC(x, y)
indicates the number of bits needed to compressxandytogether (usually, the two strings are
concatenated). Distances close to one indicate dissimilarity, while distances near zero indicate
similarity.

## Identifying musics

The main objective of this work is to develop and test a setup using the NCD for the automatic
identification of musics, using small samples for querying the database (for example, 10 seconds).
For an introduction to this topic, see the paper by Rudi Cilibrasiet al., available athttp:
//homepages.cwi.nl/~paulv/papers/music.pdf,

```
Rudi Cilibrasi, Paul Vit ́anyi, and Ronald de Wolf,Algorithmic Clustering of Music
Based on String Compression, Computer Music Journal, 28:4, pp. 49–67, 2004.
```
```
1
```

The problem can be stated as follows. Suppose that a certain database contains representations
of several (complete) musics, denotedmi, and that we want to identify a segment of music,
represented by stringx. The idea is to compute the values of NCD(x, mi),∀i, and assign tox
the name of the music in the database that yields the smallest value of the NCD.

## What to do and how to do it

```
 For compression, standard compressors, such asgzip,bzip2,lzma,zstd,... , should be
used. The report should include comparative results using several of these compressors.
 The database should contain, at least 25 different musics. Testing should be done on small
segments of the musics.
 It is also suggested to add some noise to the segments used for querying, in order to assess
the robustness of the technique.
 For manipulation of audio files, such as format conversion, extraction of segments, addition
of noise, etc., see, for example,http://sox.sourceforge.net/.
 Elaborate a poster (Horizontal A0) where you describe and demonstrate the work done
(it will be presented in a poster session on 16 Jun).
```
Note: For this approach to be successful, the audio files need to be first converted into a
representation (a kind of signature) more adequate to the general purpose compressors that
are going to be used. One of the possibilities is to transform the audio file into the set of its
most significant frequencies. Because, generally, the audio frequencies vary along time, this is
attained by first cutting the audio into (partially overlapping) segments and then compute the
most significant frequencies for each of these segments. An example, namedGetMaxFreqs, in
C++, is available in the website of the course. This example can be used as is or adapted, if
required. Of course, independent implementations will be valued.

#### 2


