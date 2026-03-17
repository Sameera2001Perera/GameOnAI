"""
Modern Code Vector Space - Best Practices 2024
Uses semantic chunking and late chunking techniques with minimal code
"""

import os
from pathlib import Path
from itertools import groupby
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


class CodeEmbeddings:
    def __init__(self):
        # Use state-of-the-art embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
    
    def populate_workspace(self, workspace_path: str):
        """Create semantic vector space from code files"""
        print(f"🔍 Creating semantic vector space: {workspace_path}")
        
        files = self._find_files(workspace_path)
        print(f"all files : {files}")
        documents = []
        
        for file_path in files:
            chunks = self._semantic_chunk_file(file_path)
            documents.extend(chunks)

        if documents:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            print(f"✅ Created vector space with {len(documents)} semantic chunks")
        
        return len(documents)
    
    def _find_files(self, workspace_path: str) -> List[str]:
        """Find exactly the files you specified"""
        root = Path(workspace_path)
        files = []
        
        for file_path in root.rglob('*'):
            if not file_path.is_file():
                continue
            
            if any(skip in file_path.parts for skip in ['node_modules', '.git', '.next', 'dist', 'build']):
                continue

            relative_path = file_path.relative_to(root)
            
            if (file_path.name == 'route.ts' and 
                'app' in file_path.parts and 'api' in file_path.parts):
                files.append(str(relative_path))
            
            elif ('pages' in file_path.parts and 'api' in file_path.parts and 
                file_path.suffix == '.ts'):
                files.append(str(relative_path))
            
            elif ('app' in file_path.parts and 'components' in file_path.parts and 
                file_path.suffix in ['.tsx', '.css']):
                files.append(str(relative_path))
            
            elif ('app' in file_path.parts and 'hooks' in file_path.parts and 
                file_path.suffix == '.ts'):
                files.append(str(relative_path))
            
            elif ('app' in file_path.parts and 'types' in file_path.parts and 
                file_path.suffix == '.ts'):
                files.append(str(relative_path))
            
            elif file_path.name == 'page.tsx':
                files.append(str(relative_path))
            
            elif file_path.name in ['global.css', 'globals.css']:
                files.append(str(relative_path))
        
        print(f"Found {len(files)} target files")
        print(f"Included files : {files}")
        return files
    def _semantic_chunk_file(self, file_path: str) -> List[Document]:
        """Use semantic chunking for better code understanding"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.css'):
                return self._chunk_css(content, file_path)
            else:
                return self._semantic_chunk_code(content, file_path)
                
        except Exception as e:
            print(f"❌ Error: {file_path}: {e}")
            return []
    
    def _semantic_chunk_code(self, content: str, file_path: str) -> List[Document]:
        """Semantic chunking for TypeScript files"""

        logical_chunks = self._extract_logical_units(content)
        
        if not logical_chunks:

            return self._recursive_chunk(content, file_path)
        
        return self._group_by_semantics(logical_chunks, file_path)
    
    def _extract_logical_units(self, content: str) -> List[str]:
        """Extract logical code units (functions, classes, exports)"""
        import re
        
        # Find function/class/interface boundaries
        patterns = [
            # Functions
            r'((?:export\s+)?(?:async\s+)?function\s+\w+[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\})',
            # Arrow functions  
            r'((?:export\s+)?const\s+\w+\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\})',
            # Classes
            r'((?:export\s+)?class\s+\w+[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\})',
            # Interfaces/Types
            r'((?:export\s+)?(?:interface|type)\s+\w+[^;{]*(?:\{[^{}]*\}|[^;]*;))',
            # Default exports
            r'(export\s+default\s+[^;]+;?)',
        ]
        
        chunks = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            chunks.extend(matches)
        
        # Remove duplicates and filter valid chunks
        unique_chunks = []
        seen = set()
        for chunk in chunks:
            chunk_clean = chunk.strip()
            if len(chunk_clean) > 50 and chunk_clean not in seen:  # Minimum size filter
                unique_chunks.append(chunk_clean)
                seen.add(chunk_clean)
        
        return unique_chunks
    
    def _group_by_semantics(self, chunks: List[str], file_path: str) -> List[Document]:
        """Group chunks by semantic similarity"""
        if len(chunks) <= 1:
            return [Document(
                page_content=chunks[0] if chunks else "",
                metadata={'file_path': file_path, 'filename': Path(file_path).name}
            )]
        
        # Generate embeddings for each chunk
        chunk_embeddings = self.embeddings.embed_documents(chunks)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(chunk_embeddings)
        
        # Group similar chunks (threshold-based)
        threshold = 0.7  # Adjust based on your needs
        groups = self._cluster_by_similarity(similarity_matrix, threshold)
        
        # Create documents from groups
        documents = []
        for i, group in enumerate(groups):
            # Combine chunks in the same group
            combined_content = '\n\n'.join([chunks[idx] for idx in group])
            
            doc = Document(
                page_content=combined_content,
                metadata={
                    'file_path': file_path,
                    'filename': Path(file_path).name,
                    'chunk_group': i,
                    'chunk_count': len(group)
                }
            )
            documents.append(doc)
        
        return documents
    
    def _cluster_by_similarity(self, similarity_matrix: np.ndarray, threshold: float) -> List[List[int]]:
        """Simple clustering based on similarity threshold"""
        n = similarity_matrix.shape[0]
        visited = [False] * n
        groups = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            # Start new group
            group = [i]
            visited[i] = True
            
            # Find similar chunks
            for j in range(i + 1, n):
                if not visited[j] and similarity_matrix[i][j] > threshold:
                    group.append(j)
                    visited[j] = True
            
            groups.append(group)
        
        return groups
    
    def _recursive_chunk(self, content: str, file_path: str) -> List[Document]:
        """Fallback recursive chunking"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = splitter.split_text(content)
        return [
            Document(
                page_content=chunk,
                metadata={
                    'file_path': file_path,
                    'filename': Path(file_path).name,
                    'chunk_index': i
                }
            )
            for i, chunk in enumerate(chunks)
        ]
    
    def _chunk_css(self, content: str, file_path: str) -> List[Document]:
        """Simple CSS chunking"""
        return [Document(
            page_content=content,
            metadata={
                'file_path': file_path,
                'filename': Path(file_path).name,
                'file_type': 'css'
            }
        )]
        
    def search(self, query: str, k: int = 10) -> List[Dict]:
            """Semantic search"""
            if not self.vectorstore:
                raise ValueError("Vector store not created")
            
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)

            results = []
            for doc, distance in docs_and_scores:
      
                relevance_score = max(0.0, 1.0 - (distance / 2.0))
                
                results.append({
                    'file_path': doc.metadata['file_path'],
                    'filename': doc.metadata['filename'],
                    'score': relevance_score, 
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
            return results
        
    def save(self, path: str):
        if self.vectorstore:
            self.vectorstore.save_local(path)
    
    def load(self, path: str):
        self.vectorstore = FAISS.load_local(path, self.embeddings)
    
    def get_uniques(self, results):

        return [max(group, key=lambda x: x['score']) 
                        for _, group in groupby(sorted(results, key=lambda x: x['file_path']), 
                                            key=lambda x: x['file_path'])]



def main():
    embedder = CodeEmbeddings()
    
    workspace_path = Path(os.path.join(os.getcwd(), "workspace"))
    

    chunk_count = embedder.populate_workspace(workspace_path)
    
    if chunk_count > 0:
        query = "the websocket is not connecting between two players"
            
            


        
        print("\n🔍 Semantic search results:")
        print("=" * 50)
        

        print(f"\nQuery: '{query}'")
        results = embedder.search(query, k=7)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} - Score: {result['score']:.3f}")
            print(f"     {result['file_path']}")
            if 'chunk_group' in result['metadata']:
                print(f"     Semantic group: {result['metadata']['chunk_group']}")




       

if __name__ == "__main__":
    main()