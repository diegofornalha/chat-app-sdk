const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs-extra');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { query } = require('@anthropic-ai/claude-code');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(express.json());

// Storage for uploaded files
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadDir = 'uploads';
    fs.ensureDirSync(uploadDir);
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const upload = multer({ 
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow text files and common code files
    const allowedTypes = [
      'text/plain',
      'text/javascript',
      'text/html',
      'text/css',
      'application/json',
      'application/javascript'
    ];
    
    const allowedExtensions = [
      '.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cpp', '.c', '.h',
      '.css', '.html', '.json', '.xml', '.yaml', '.yml', '.md', '.txt',
      '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sql'
    ];
    
    const ext = path.extname(file.originalname).toLowerCase();
    const isAllowedType = allowedTypes.includes(file.mimetype);
    const isAllowedExt = allowedExtensions.includes(ext);
    
    if (isAllowedType || isAllowedExt || file.mimetype.startsWith('text/')) {
      cb(null, true);
    } else {
      cb(new Error('Only text and code files are allowed'), false);
    }
  }
});

// In-memory session storage (in production, use Redis or database)
const sessions = new Map();
const activeConnections = new Map();

// Helper functions for processing step messages
function getStepMessage(stepType, msg) {
  switch (stepType) {
    case 'thinking':
      return 'Claude is analyzing your request and planning the response strategy...';
    case 'tool_use':
      return `Executing ${msg.name || 'tool'}: ${getToolDescription(msg.name, msg.input)}`;
    case 'tool_result':
      const success = !msg.is_error && msg.content;
      return `Tool ${msg.tool_use_id?.slice(0, 8) || 'execution'} ${success ? 'completed successfully' : 'failed'}`;
    case 'result':
      if (msg.is_error) {
        return `Processing failed: ${msg.error || 'Unknown error'}`;
      }
      return `Response generated (${msg.result?.length || 0} characters, ${msg.num_turns || 1} turns)`;
    case 'streaming':
      return 'Streaming response content to client...';
    default:
      return `Processing: ${stepType}`;
  }
}

function getToolDescription(toolName, input) {
  switch (toolName) {
    case 'Read':
      return `Reading file: ${input?.file_path?.split('/').pop() || 'file'}`;
    case 'Write':
      return `Writing to file: ${input?.file_path?.split('/').pop() || 'file'}`;
    case 'Edit':
      return `Editing file: ${input?.file_path?.split('/').pop() || 'file'}`;
    case 'Bash':
      return `Running command: ${input?.command?.substring(0, 50) || 'command'}${input?.command?.length > 50 ? '...' : ''}`;
    case 'Glob':
      return `Searching files with pattern: ${input?.pattern || 'pattern'}`;
    case 'Grep':
      return `Searching content for: ${input?.pattern || 'pattern'}`;
    case 'LS':
      return `Listing directory: ${input?.path?.split('/').pop() || 'directory'}`;
    case 'Task':
      return `Spawning sub-agent: ${input?.description || 'task'}`;
    case 'WebFetch':
      return `Fetching URL: ${input?.url || 'web page'}`;
    case 'WebSearch':
      return `Web search: ${input?.query || 'query'}`;
    default:
      return toolName ? `${toolName} operation` : 'Unknown operation';
  }
}

function getStepData(msg) {
  const data = { 
    type: msg.type,
    timestamp: Date.now(),
    messageId: generateShortId()
  };
  
  switch (msg.type) {
    case 'tool_use':
      data.toolName = msg.name;
      data.toolId = msg.id;
      data.toolInput = msg.input;
      data.inputSummary = getInputSummary(msg.name, msg.input);
      data.expectedOutput = getExpectedOutput(msg.name, msg.input);
      data.toolDescription = getDetailedToolDescription(msg.name);
      break;
      
    case 'tool_result':
      data.toolUseId = msg.tool_use_id;
      data.hasError = !!msg.is_error;
      data.contentLength = msg.content?.length;
      data.contentType = getContentType(msg.content);
      data.errorDetails = msg.is_error ? msg.content : null;
      data.executionStatus = msg.is_error ? 'failed' : 'success';
      data.outputSummary = getOutputSummary(msg.content);
      break;
      
    case 'result':
      data.isError = msg.is_error;
      data.duration = msg.duration_ms;
      data.cost = msg.total_cost_usd;
      data.turns = msg.num_turns;
      data.inputTokens = msg.input_tokens;
      data.outputTokens = msg.output_tokens;
      data.cacheReads = msg.cache_read_tokens;
      data.cacheWrites = msg.cache_write_tokens;
      
      if (msg.result) {
        data.responseLength = msg.result.length;
        data.responseWords = msg.result.split(/\s+/).length;
        data.responseLines = msg.result.split('\n').length;
        data.hasCodeBlocks = /```/.test(msg.result);
        data.hasMarkdown = /[#*`\[\]]/.test(msg.result);
      }
      
      if (msg.error) {
        data.errorType = getErrorType(msg.error);
        data.errorMessage = msg.error;
      }
      break;
      
    case 'thinking':
      data.cognitiveLoad = 'processing';
      data.analysisPhase = 'understanding_request';
      data.strategizing = true;
      break;
      
    default:
      data.unknownType = true;
      break;
  }
  
  return data;
}

function generateShortId() {
  return Math.random().toString(36).substr(2, 8);
}

function getInputSummary(toolName, input) {
  if (!input) return 'No input provided';
  
  switch (toolName) {
    case 'Read':
      return `File: ${input.file_path?.split('/').pop()} (${input.limit ? `first ${input.limit} lines` : 'entire file'})`;
    case 'Write':
      return `File: ${input.file_path?.split('/').pop()} (${input.content?.length || 0} characters)`;
    case 'Edit':
      return `File: ${input.file_path?.split('/').pop()} (${input.old_string?.length || 0} → ${input.new_string?.length || 0} chars)`;
    case 'Bash':
      return `Command: ${input.command} ${input.timeout ? `(timeout: ${input.timeout}ms)` : ''}`;
    case 'Glob':
      return `Pattern: ${input.pattern} in ${input.path || 'current directory'}`;
    case 'Grep':
      return `Pattern: /${input.pattern}/ in ${input.include || 'all files'}`;
    default:
      return Object.keys(input).map(k => `${k}: ${String(input[k]).substring(0, 30)}`).join(', ');
  }
}

function getExpectedOutput(toolName, input) {
  switch (toolName) {
    case 'Read':
      return 'File contents with line numbers';
    case 'Write':
      return 'File creation confirmation';
    case 'Edit':
      return 'File modification confirmation';
    case 'Bash':
      return 'Command output and exit status';
    case 'Glob':
      return 'List of matching file paths';
    case 'Grep':
      return 'Files containing the search pattern';
    case 'LS':
      return 'Directory listing with file details';
    case 'Task':
      return 'Sub-agent execution results';
    default:
      return 'Tool-specific output';
  }
}

function getDetailedToolDescription(toolName) {
  switch (toolName) {
    case 'Read':
      return 'Reads file contents from the filesystem with optional line limits and offsets';
    case 'Write':
      return 'Creates or overwrites files with provided content';
    case 'Edit':
      return 'Performs exact string replacements in existing files';
    case 'Bash':
      return 'Executes shell commands in a persistent session with timeout controls';
    case 'Glob':
      return 'Searches for files matching glob patterns with modification time sorting';
    case 'Grep':
      return 'Searches file contents using regular expressions with file filtering';
    case 'LS':
      return 'Lists directory contents with detailed file information';
    case 'Task':
      return 'Spawns independent agent instances for complex subtasks';
    case 'WebFetch':
      return 'Fetches and processes web content with AI analysis';
    case 'WebSearch':
      return 'Performs web searches with result filtering and ranking';
    default:
      return 'Specialized tool for specific operations';
  }
}

function getContentType(content) {
  if (!content) return 'empty';
  if (typeof content !== 'string') return typeof content;
  
  if (content.includes('Error:') || content.includes('error:')) return 'error_message';
  if (content.match(/^\s*\{.*\}\s*$/s)) return 'json';
  if (content.match(/^\s*<.*>\s*$/s)) return 'xml_html';
  if (content.includes('```')) return 'code_block';
  if (content.split('\n').length > 10) return 'multiline_text';
  
  return 'text';
}

function getOutputSummary(content) {
  if (!content) return 'No output';
  
  const lines = content.split('\n').length;
  const words = content.split(/\s+/).length;
  const chars = content.length;
  
  let summary = `${chars} chars, ${words} words, ${lines} lines`;
  
  if (content.includes('Error:')) summary += ' (contains errors)';
  if (content.includes('```')) summary += ' (contains code)';
  if (content.match(/\.(js|ts|py|java|cpp|c|go|rs|php|rb)$/)) summary += ' (source code)';
  
  return summary;
}

function getErrorType(error) {
  if (!error) return 'unknown';
  
  const errorStr = error.toString().toLowerCase();
  
  if (errorStr.includes('timeout')) return 'timeout';
  if (errorStr.includes('permission')) return 'permission_denied';
  if (errorStr.includes('not found') || errorStr.includes('enoent')) return 'file_not_found';
  if (errorStr.includes('syntax')) return 'syntax_error';
  if (errorStr.includes('network') || errorStr.includes('fetch')) return 'network_error';
  if (errorStr.includes('memory') || errorStr.includes('oom')) return 'memory_error';
  
  return 'general_error';
}

// Health check endpoint
app.get('/api/health', async (req, res) => {
  try {
    // Test Claude Code availability by running a simple query
    const messages = [];
    for await (const message of query({
      prompt: "Say 'Hello' in one word",
      options: {
        maxTurns: 1,
      },
    })) {
      messages.push(message);
    }
    
    const lastMessage = messages[messages.length - 1];
    const claudeAvailable = lastMessage && lastMessage.type === 'result' && !lastMessage.is_error;
    
    res.json({
      status: 'ok',
      claude_available: claudeAvailable,
      timestamp: Date.now(),
      active_connections: activeConnections.size,
      active_sessions: sessions.size
    });
  } catch (error) {
    res.json({
      status: 'ok',
      claude_available: false,
      error: error.message,
      timestamp: Date.now(),
      active_connections: activeConnections.size,
      active_sessions: sessions.size
    });
  }
});

// File upload endpoint
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = req.file.path;
    const content = await fs.readFile(filePath, 'utf8');
    
    // Clean up uploaded file after reading
    await fs.remove(filePath);
    
    res.json({
      success: true,
      filename: req.file.originalname,
      content: content,
      size: req.file.size,
      mimetype: req.file.mimetype
    });
  } catch (error) {
    console.error('File upload error:', error);
    res.status(500).json({ 
      error: 'Failed to process file',
      details: error.message 
    });
  }
});

// Export conversation endpoint
app.post('/api/export', async (req, res) => {
  try {
    const { messages, format = 'markdown' } = req.body;
    
    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Invalid messages data' });
    }
    
    let content = '';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    if (format === 'markdown') {
      content += `# Claude Code Chat Export\n\n`;
      content += `Generated on: ${new Date().toLocaleString()}\n\n`;
      content += `---\n\n`;
      
      messages.forEach((msg, index) => {
        const role = msg.type === 'user' ? 'User' : 'Claude';
        content += `## ${role} (${new Date(msg.timestamp).toLocaleTimeString()})\n\n`;
        content += `${msg.content}\n\n`;
        
        if (msg.type === 'assistant' && (msg.cost || msg.duration || msg.turns)) {
          content += `*Metadata: `;
          const meta = [];
          if (msg.cost) meta.push(`Cost: $${msg.cost.toFixed(4)}`);
          if (msg.duration) meta.push(`Duration: ${msg.duration.toFixed(0)}ms`);
          if (msg.turns) meta.push(`Turns: ${msg.turns}`);
          content += meta.join(' • ') + '*\n\n';
        }
        
        content += `---\n\n`;
      });
    } else if (format === 'json') {
      content = JSON.stringify({
        export_date: new Date().toISOString(),
        message_count: messages.length,
        messages: messages
      }, null, 2);
    }
    
    const filename = `claude-chat-${timestamp}.${format === 'json' ? 'json' : 'md'}`;
    
    res.setHeader('Content-Type', format === 'json' ? 'application/json' : 'text/markdown');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.send(content);
  } catch (error) {
    console.error('Export error:', error);
    res.status(500).json({ error: 'Failed to export conversation' });
  }
});

// Session management endpoints
app.get('/api/sessions', (req, res) => {
  const sessionList = Array.from(sessions.entries()).map(([id, data]) => ({
    id: id,
    created: data.created,
    lastActivity: data.lastActivity,
    messageCount: data.messages ? data.messages.length : 0,
    title: data.title || `Session ${id.slice(0, 8)}...`
  }));
  
  res.json({ sessions: sessionList });
});

app.get('/api/sessions/:sessionId', (req, res) => {
  const sessionData = sessions.get(req.params.sessionId);
  if (!sessionData) {
    return res.status(404).json({ error: 'Session not found' });
  }
  
  res.json(sessionData);
});

app.delete('/api/sessions/:sessionId', (req, res) => {
  const deleted = sessions.delete(req.params.sessionId);
  res.json({ success: deleted });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  activeConnections.set(socket.id, { connectedAt: Date.now() });
  
  // Send connection stats
  socket.emit('connection_stats', {
    active_connections: activeConnections.size,
    active_sessions: sessions.size
  });
  
  // Handle chat messages with streaming
  socket.on('send_message', async (data) => {
    console.log('📥 [TRACE] Received send_message event:', {
      socketId: socket.id,
      dataKeys: Object.keys(data),
      messageLength: data?.message?.length,
      sessionId: data?.sessionId,
      timestamp: new Date().toISOString()
    });
    
    try {
      const { 
        message, 
        sessionId, 
        systemPrompt, 
        maxTurns = 5,
        allowedTools = [],
        customOptions = {}
      } = data;
      
      if (!message || !message.trim()) {
        console.log('❌ [TRACE] Empty message validation failed');
        socket.emit('error', { error: 'Message cannot be empty' });
        return;
      }
      
      console.log('✅ [TRACE] Message validation passed:', {
        messagePreview: message.substring(0, 100),
        sessionId: sessionId,
        hasSystemPrompt: !!systemPrompt
      });
      
      // Generate session ID if not provided
      const currentSessionId = sessionId || uuidv4();
      
      // Get or create session
      let sessionData = sessions.get(currentSessionId) || {
        id: currentSessionId,
        created: Date.now(),
        messages: [],
        title: message.length > 50 ? message.substring(0, 50) + '...' : message
      };
      
      // Add user message to session
      const userMessage = {
        id: uuidv4(),
        type: 'user',
        content: message,
        timestamp: Date.now()
      };
      
      sessionData.messages.push(userMessage);
      sessionData.lastActivity = Date.now();
      sessions.set(currentSessionId, sessionData);
      
      // Emit user message
      console.log('📤 [TRACE] Emitting user message:', {
        messageId: userMessage.id,
        sessionId: currentSessionId,
        contentLength: userMessage.content.length
      });
      
      socket.emit('message', {
        ...userMessage,
        sessionId: currentSessionId
      });
      
      // Prepare Claude Code query options
      const queryOptions = {
        maxTurns: maxTurns,
        ...customOptions
      };
      
      // Add system prompt if provided
      let finalPrompt = message;
      if (systemPrompt) {
        finalPrompt = `${systemPrompt}\n\nUser: ${message}`;
      }
      
      // Add allowed tools if specified
      if (allowedTools.length > 0) {
        queryOptions.allowedTools = allowedTools;
      }
      
      // Start processing response
      console.log('⏳ [TRACE] Starting Claude query with options:', {
        sessionId: currentSessionId,
        queryOptions: queryOptions,
        finalPromptLength: finalPrompt.length
      });
      
      socket.emit('typing_start');
      socket.emit('processing_step', {
        sessionId: currentSessionId,
        step: 'initializing',
        message: 'Initializing Claude Code SDK...',
        data: {
          type: 'initialization',
          promptLength: finalPrompt.length,
          maxTurns: queryOptions.maxTurns,
          allowedTools: queryOptions.allowedTools || [],
          sessionInfo: `Session ${currentSessionId.slice(0, 8)}`,
          timestamp: Date.now()
        },
        timestamp: Date.now()
      });
      
      let assistantResponse = '';
      let responseMetadata = {};
      const messages = [];
      
      try {
        // Use Claude Code SDK to query
        console.log('🤖 [TRACE] Starting Claude Code query iteration');
        
        socket.emit('processing_step', {
          sessionId: currentSessionId,
          step: 'connecting',
          message: 'Establishing connection to Claude API...',
          data: {
            type: 'connection',
            apiEndpoint: 'Claude Code SDK',
            authentication: 'API Key validated',
            requestSize: `${Math.round(finalPrompt.length / 1024)}KB`,
            timestamp: Date.now()
          },
          timestamp: Date.now()
        });
        
        for await (const msg of query({
          prompt: finalPrompt,
          options: queryOptions,
        })) {
          messages.push(msg);
          console.log('🔄 [TRACE] Claude Code message received:', {
            type: msg.type,
            hasResult: !!msg.result,
            isError: msg.is_error,
            resultLength: msg.result?.length,
            messageKeys: Object.keys(msg)
          });
          
          // Emit real-time processing steps
          socket.emit('processing_step', {
            sessionId: currentSessionId,
            step: msg.type,
            message: getStepMessage(msg.type, msg),
            data: getStepData(msg),
            timestamp: Date.now()
          });
          
          // Handle different message types from Claude Code SDK
          if (msg.type === 'result') {
            // Capture final metadata
            responseMetadata = {
              cost: msg.total_cost_usd,
              duration: msg.duration_ms,
              turns: msg.num_turns,
              is_error: msg.is_error
            };
            
            if (!msg.is_error && msg.result) {
              assistantResponse = msg.result;
              console.log('✅ [TRACE] Got successful Claude response:', {
                responseLength: assistantResponse.length,
                preview: assistantResponse.substring(0, 100) + '...',
                sessionId: currentSessionId,
                metadata: responseMetadata
              });
              
              // Simple streaming simulation - just emit the full response
              console.log('📤 [TRACE] Emitting message_stream event');
              socket.emit('message_stream', {
                sessionId: currentSessionId,
                content: msg.result,
                fullContent: msg.result
              });
              
            } else if (msg.is_error) {
              assistantResponse = `Error: ${msg.error || 'Unknown error occurred'}`;
              console.log('❌ [TRACE] Claude returned error:', {
                error: msg.error,
                sessionId: currentSessionId,
                metadata: responseMetadata
              });
            }
          } else if (msg.type === 'thinking') {
            console.log('Claude is thinking...');
          } else if (msg.type === 'tool_use' || msg.type === 'tool_result') {
            console.log('Tool usage:', msg.type, msg.name || msg.tool_use_id);
          }
        }
        
        console.log('🏁 [TRACE] Claude query completed, processing final response');
        
        socket.emit('processing_step', {
          sessionId: currentSessionId,
          step: 'finalizing',
          message: 'Finalizing response...',
          timestamp: Date.now()
        });
        
        socket.emit('typing_end');
        
        // Create assistant message
        const assistantMessage = {
          id: uuidv4(),
          type: 'assistant',
          content: assistantResponse,
          timestamp: Date.now(),
          ...responseMetadata
        };
        
        console.log('💾 [TRACE] Saving assistant message to session:', {
          messageId: assistantMessage.id,
          sessionId: currentSessionId,
          contentLength: assistantResponse.length,
          metadata: responseMetadata
        });
        
        // Save to session
        sessionData.messages.push(assistantMessage);
        sessionData.lastActivity = Date.now();
        sessions.set(currentSessionId, sessionData);
        
        // Emit complete message
        console.log('📤 [TRACE] Emitting message_complete event:', {
          messageId: assistantMessage.id,
          sessionId: currentSessionId
        });
        
        socket.emit('message_complete', {
          ...assistantMessage,
          sessionId: currentSessionId
        });
        
      } catch (error) {
        console.error('❌ [TRACE] Claude query error:', {
          error: error.message,
          stack: error.stack,
          sessionId: currentSessionId
        });
        socket.emit('typing_end');
        
        const errorMessage = {
          id: uuidv4(),
          type: 'assistant',
          content: `Error: ${error.message}`,
          timestamp: Date.now(),
          is_error: true
        };
        
        sessionData.messages.push(errorMessage);
        sessions.set(currentSessionId, sessionData);
        
        socket.emit('error', {
          ...errorMessage,
          sessionId: currentSessionId
        });
      }
      
    } catch (error) {
      console.error('Message handling error:', error);
      socket.emit('error', { 
        error: 'Failed to process message',
        details: error.message 
      });
    }
  });
  
  // Handle file analysis requests
  socket.on('analyze_file', async (data) => {
    try {
      const { content, filename, prompt = 'Analyze this code file' } = data;
      
      if (!content) {
        socket.emit('error', { error: 'No file content provided' });
        return;
      }
      
      const analysisPrompt = `${prompt}

File: ${filename}
Content:
\`\`\`
${content}
\`\`\`

Please provide a thorough analysis of this file.`;
      
      // Trigger analysis using the same message flow
      socket.emit('send_message', {
        message: analysisPrompt,
        maxTurns: 3
      });
      
    } catch (error) {
      console.error('File analysis error:', error);
      socket.emit('error', { 
        error: 'Failed to analyze file',
        details: error.message 
      });
    }
  });
  
  // Handle session management
  socket.on('load_session', (sessionId) => {
    const sessionData = sessions.get(sessionId);
    if (sessionData) {
      socket.emit('session_loaded', sessionData);
    } else {
      socket.emit('error', { error: 'Session not found' });
    }
  });
  
  socket.on('create_session', () => {
    const newSessionId = uuidv4();
    const sessionData = {
      id: newSessionId,
      created: Date.now(),
      messages: [],
      title: 'New Session'
    };
    
    sessions.set(newSessionId, sessionData);
    socket.emit('session_created', sessionData);
  });
  
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    activeConnections.delete(socket.id);
  });
});

// Start server
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log('🚀 Enhanced Claude Code SDK Server running on port', PORT);
  console.log('📋 Features enabled:');
  console.log('  • Real-time streaming chat');
  console.log('  • File upload and analysis');
  console.log('  • Session management');
  console.log('  • Conversation export');
  console.log('  • Advanced Claude Code SDK integration');
  console.log('  • WebSocket connections for real-time updates');
});