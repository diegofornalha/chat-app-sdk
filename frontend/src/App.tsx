import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { io, Socket } from 'socket.io-client';

// Anthropic-inspired color system
const colors = {
  // Backgrounds
  background: '#F2EFEB',
  surface: '#FFFFFF',
  surfaceSecondary: '#FAFAFA',
  surfaceTertiary: '#F5F5F5',
  
  // Text
  textPrimary: '#000000',
  textSecondary: '#525252',
  textTertiary: '#A9A9A9',
  
  // Borders
  border: '#E0E0E0',
  borderLight: '#F0F0F0',
  borderFocus: '#A2C3D2',
  
  // Accent colors
  accent: '#A2C3D2',
  accentHover: '#8BB0C7',
  accentLight: '#D4E6ED',
  
  // Success/Green
  success: '#A0C090',
  successHover: '#8BC34A',
  successLight: '#E8F5E8',
  
  // Warning/Purple
  warning: '#C4B5D3',
  warningHover: '#B8A5CC',
  warningLight: '#F0EBFF',
  
  // Error/Red
  error: '#E98F75',
  errorHover: '#E67B5B',
  errorLight: '#FDEAE6',
  
  // Status
  statusSuccess: '#8BC34A',
  statusWarning: '#A9A9A9',
  statusError: '#E98F75',
  
  // Interactive states
  hover: '#F5F5F5',
  active: '#E8E8E8',
  disabled: '#A9A9A9',
  
  // Overlays
  overlay: 'rgba(0, 0, 0, 0.4)',
  overlayLight: 'rgba(0, 0, 0, 0.1)',
};

// Custom syntax highlighting theme matching Anthropic colors
const customSyntaxTheme = {
  'code[class*="language-"]': {
    color: colors.textPrimary,
    background: colors.surfaceTertiary,
    textShadow: 'none',
    fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
    fontSize: '14px',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    wordWrap: 'normal',
    lineHeight: '1.5',
    tabSize: '4',
    hyphens: 'none',
  },
  'pre[class*="language-"]': {
    color: colors.textPrimary,
    background: colors.surfaceTertiary,
    textShadow: 'none',
    fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
    fontSize: '14px',
    textAlign: 'left',
    whiteSpace: 'pre',
    wordSpacing: 'normal',
    wordBreak: 'normal',
    wordWrap: 'normal',
    lineHeight: '1.5',
    tabSize: '4',
    hyphens: 'none',
    padding: '16px',
    margin: '8px 0',
    overflow: 'auto',
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
  },
  // Syntax highlighting colors
  'comment': { color: colors.textTertiary, fontStyle: 'italic' },
  'prolog': { color: colors.textTertiary, fontStyle: 'italic' },
  'doctype': { color: colors.textTertiary, fontStyle: 'italic' },
  'cdata': { color: colors.textTertiary, fontStyle: 'italic' },
  'punctuation': { color: colors.textPrimary },
  'property': { color: colors.accent },
  'tag': { color: colors.success },
  'boolean': { color: colors.warning },
  'number': { color: colors.warning },
  'constant': { color: colors.warning },
  'symbol': { color: colors.warning },
  'deleted': { color: colors.error },
  'selector': { color: colors.successHover },
  'attr-name': { color: colors.accent },
  'string': { color: colors.successHover },
  'char': { color: colors.successHover },
  'builtin': { color: colors.accent },
  'inserted': { color: colors.successHover },
  'operator': { color: colors.textPrimary },
  'entity': { color: colors.accent },
  'url': { color: colors.accent },
  'keyword': { color: colors.warning, fontWeight: 'bold' },
  'atrule': { color: colors.warning },
  'attr-value': { color: colors.successHover },
  'function': { color: colors.accent, fontWeight: 'bold' },
  'class-name': { color: colors.success, fontWeight: 'bold' },
  'regex': { color: colors.successHover },
  'important': { color: colors.error, fontWeight: 'bold' },
  'variable': { color: colors.textPrimary },
  'namespace': { color: colors.textTertiary },
};

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: number;
  cost?: number;
  duration?: number;
  turns?: number;
  is_error?: boolean;
}

interface Session {
  id: string;
  created: number;
  lastActivity: number;
  messageCount: number;
  title: string;
  messages?: Message[];
}

interface FileUploadResult {
  success: boolean;
  filename: string;
  content: string;
  size: number;
  mimetype: string;
}

interface ChatSettings {
  systemPrompt: string;
  maxTurns: number;
  allowedTools: string[];
  streamingEnabled: boolean;
}

interface ConnectionStats {
  active_connections: number;
  active_sessions: number;
}

interface ProcessingStep {
  sessionId: string;
  step: string;
  message: string;
  data?: any;
  timestamp: number;
}

const API_BASE = 'http://localhost:8080/api';

// Reusable button component with consistent styling
const HeaderButton = ({ 
  children, 
  onClick, 
  active = false, 
  variant = 'default',
  ...props 
}: {
  children: React.ReactNode;
  onClick: () => void;
  active?: boolean;
  variant?: 'default' | 'success' | 'danger';
  [key: string]: any;
}) => {
  const getVariantColors = () => {
    switch (variant) {
      case 'success':
        return {
          bg: active ? colors.success : 'transparent',
          hoverBg: active ? colors.successHover : colors.hover,
          border: active ? colors.success : colors.border,
          text: active ? colors.surface : colors.textPrimary,
          focus: colors.successLight
        };
      case 'danger':
        return {
          bg: active ? colors.error : 'transparent',
          hoverBg: active ? colors.errorHover : colors.hover,
          border: active ? colors.error : colors.border,
          text: active ? colors.surface : colors.textPrimary,
          focus: colors.errorLight
        };
      default:
        return {
          bg: active ? colors.accent : 'transparent',
          hoverBg: active ? colors.accentHover : colors.hover,
          border: active ? colors.accent : colors.border,
          text: active ? colors.surface : colors.textPrimary,
          focus: colors.accentLight
        };
    }
  };

  const variantColors = getVariantColors();

  return (
    <button
      onClick={onClick}
      className="text-sm px-3 py-1.5 rounded-md transition-all duration-200 font-medium focus:outline-none"
      style={{ 
        color: variantColors.text,
        border: `1px solid ${variantColors.border}`,
        backgroundColor: variantColors.bg,
        boxShadow: active ? `0 2px 4px ${colors.overlayLight}` : 'none'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = variantColors.hoverBg;
        if (!active) e.currentTarget.style.borderColor = variantColors.border === colors.border ? colors.accent : variantColors.border;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = variantColors.bg;
        e.currentTarget.style.borderColor = variantColors.border;
      }}
      onFocus={(e) => {
        e.currentTarget.style.outline = 'none';
        e.currentTarget.style.boxShadow = `0 0 0 2px ${variantColors.focus}`;
      }}
      onBlur={(e) => {
        e.currentTarget.style.boxShadow = active ? `0 2px 4px ${colors.overlayLight}` : 'none';
      }}
      {...props}
    >
      {children}
    </button>
  );
};

// Custom code block component with copy functionality
const CodeBlock = ({ children, className, ...props }: any) => {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  if (language) {
    return (
      <div className="relative group">
        <button
          onClick={copyToClipboard}
          className="absolute top-2 right-2 px-2 py-1 text-xs rounded opacity-0 group-hover:opacity-100 transition-all duration-200"
          style={{ 
            backgroundColor: copied ? colors.statusSuccess : colors.textTertiary,
            color: colors.surface,
            boxShadow: copied ? `0 2px 4px ${colors.overlayLight}` : 'none'
          }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
        <SyntaxHighlighter
          language={language}
          style={customSyntaxTheme}
          {...props}
        >
          {children}
        </SyntaxHighlighter>
      </div>
    );
  }

  return (
    <code
      className="px-1 py-0.5 rounded text-sm"
      style={{ 
        backgroundColor: colors.warningLight,
        color: colors.textPrimary,
        border: `1px solid ${colors.borderLight}`
      }}
      {...props}
    >
      {children}
    </code>
  );
};

// Custom markdown components with Anthropic styling
const MarkdownComponents = {
  code: CodeBlock,
  pre: ({ children }: any) => <div>{children}</div>,
  h1: ({ children }: any) => (
    <h1 className="text-2xl font-bold mb-4 mt-6" style={{ color: colors.textPrimary }}>
      {children}
    </h1>
  ),
  h2: ({ children }: any) => (
    <h2 className="text-xl font-bold mb-3 mt-5" style={{ color: colors.textPrimary }}>
      {children}
    </h2>
  ),
  h3: ({ children }: any) => (
    <h3 className="text-lg font-bold mb-2 mt-4" style={{ color: colors.textPrimary }}>
      {children}
    </h3>
  ),
  p: ({ children }: any) => (
    <p className="mb-3 leading-relaxed" style={{ color: colors.textPrimary }}>
      {children}
    </p>
  ),
  ul: ({ children }: any) => (
    <ul className="list-disc list-inside mb-3 ml-4" style={{ color: colors.textPrimary }}>
      {children}
    </ul>
  ),
  ol: ({ children }: any) => (
    <ol className="list-decimal list-inside mb-3 ml-4" style={{ color: colors.textPrimary }}>
      {children}
    </ol>
  ),
  li: ({ children }: any) => (
    <li className="mb-1" style={{ color: colors.textPrimary }}>
      {children}
    </li>
  ),
  a: ({ href, children }: any) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="underline hover:no-underline transition-colors"
      style={{ color: colors.accent }}
    >
      {children}
    </a>
  ),
  blockquote: ({ children }: any) => (
    <blockquote
      className="border-l-4 pl-4 py-2 mb-3 italic"
      style={{ 
        borderLeftColor: colors.success,
        backgroundColor: colors.successLight,
        color: colors.textSecondary
      }}
    >
      {children}
    </blockquote>
  ),
  table: ({ children }: any) => (
    <div className="overflow-x-auto mb-3">
      <table className="min-w-full border-collapse" style={{ border: `1px solid ${colors.border}` }}>
        {children}
      </table>
    </div>
  ),
  th: ({ children }: any) => (
    <th
      className="border px-3 py-2 text-left font-semibold"
      style={{ 
        borderColor: colors.border,
        backgroundColor: colors.surfaceSecondary,
        color: colors.textPrimary
      }}
    >
      {children}
    </th>
  ),
  td: ({ children }: any) => (
    <td
      className="border px-3 py-2"
      style={{ 
        borderColor: colors.border,
        color: colors.textPrimary
      }}
    >
      {children}
    </td>
  ),
  strong: ({ children }: any) => (
    <strong className="font-bold" style={{ color: colors.textPrimary }}>
      {children}
    </strong>
  ),
  em: ({ children }: any) => (
    <em className="italic" style={{ color: colors.textPrimary }}>
      {children}
    </em>
  )
};

export default function ClaudeChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [connected, setConnected] = useState<boolean | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentStreamingContent, setCurrentStreamingContent] = useState('');
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [connectionStats, setConnectionStats] = useState<ConnectionStats>({ active_connections: 0, active_sessions: 0 });
  const [settings, setSettings] = useState<ChatSettings>({
    systemPrompt: '',
    maxTurns: 5,
    allowedTools: [],
    streamingEnabled: true
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamingContent]);

  useEffect(() => {
    initializeSocket();
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  // Trace messages state changes
  useEffect(() => {
    console.log('🔄 [TRACE] Messages state updated:', {
      messageCount: messages.length,
      lastMessage: messages[messages.length - 1],
      timestamp: new Date().toISOString()
    });
  }, [messages]);

  // Trace streaming content changes
  useEffect(() => {
    if (currentStreamingContent) {
      console.log('🌊 [TRACE] Streaming content updated:', {
        contentLength: currentStreamingContent.length,
        preview: currentStreamingContent.substring(0, 100) + '...',
        timestamp: new Date().toISOString()
      });
    } else {
      console.log('🛑 [TRACE] Streaming content cleared');
    }
  }, [currentStreamingContent]);

  // Trace loading state changes
  useEffect(() => {
    console.log('⏳ [TRACE] Loading state changed:', {
      loading: loading,
      timestamp: new Date().toISOString()
    });
  }, [loading]);

  // Trace processing steps changes
  useEffect(() => {
    console.log('🔄 [TRACE] Processing steps updated:', {
      stepCount: processingSteps.length,
      steps: processingSteps.map(s => ({ step: s.step, message: s.message })),
      timestamp: new Date().toISOString()
    });
  }, [processingSteps]);

  const initializeSocket = () => {
    const newSocket = io('http://localhost:8080');
    
    newSocket.on('connect', () => {
      console.log('🔗 [TRACE] Connected to server');
      setConnected(true);
      checkHealth();
    });
    
    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setConnected(false);
    });
    
    newSocket.on('connection_stats', (stats: ConnectionStats) => {
      setConnectionStats(stats);
    });
    
    newSocket.on('message', (message: Message & { sessionId: string }) => {
      console.log('📥 [TRACE] Received message event:', {
        messageId: message.id,
        type: message.type,
        contentLength: message.content?.length,
        sessionId: message.sessionId,
        timestamp: new Date().toISOString()
      });
      
      setMessages(prev => [...prev, message]);
      setSessionId(message.sessionId);
    });
    
    newSocket.on('message_stream', (data: { sessionId: string; content: string; fullContent: string }) => {
      console.log('🌊 [TRACE] Received message_stream event:', {
        sessionId: data.sessionId,
        contentLength: data.content?.length,
        fullContentLength: data.fullContent?.length,
        timestamp: new Date().toISOString()
      });
      
      setCurrentStreamingContent(data.fullContent);
    });
    
    newSocket.on('message_complete', (message: Message & { sessionId: string }) => {
      console.log('✅ [TRACE] Received message_complete event:', {
        messageId: message.id,
        contentLength: message.content?.length,
        sessionId: message.sessionId,
        cost: message.cost,
        duration: message.duration,
        turns: message.turns,
        timestamp: new Date().toISOString()
      });
      
      setCurrentStreamingContent('');
      setLoading(false);
      setMessages(prev => {
        console.log('🔄 [TRACE] Updating messages state with complete message');
        // Replace any partial streaming message with the complete one
        const filtered = prev.filter(m => m.type !== 'assistant' || !m.content.includes('...'));
        return [...filtered, message];
      });
      setSessionId(message.sessionId);
    });
    
    
    newSocket.on('error', (error: any) => {
      console.error('❌ [TRACE] Socket error received:', {
        error: error.error,
        details: error.details,
        sessionId: error.sessionId,
        timestamp: new Date().toISOString()
      });
      
      setLoading(false);
      setCurrentStreamingContent('');
      
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Error: ${error.error || error.details || 'Unknown error'}`,
        timestamp: Date.now(),
        is_error: true
      };
      
      console.log('📝 [TRACE] Adding error message to state:', errorMessage);
      setMessages(prev => [...prev, errorMessage]);
    });
    
    newSocket.on('session_created', (session: Session) => {
      setSessionId(session.id);
      setSessions(prev => [session, ...prev]);
    });
    
    newSocket.on('session_loaded', (session: Session) => {
      if (session.messages) {
        setMessages(session.messages);
        setSessionId(session.id);
      }
    });

    newSocket.on('processing_step', (step: ProcessingStep) => {
      console.log('🔄 [TRACE] Received processing step:', step);
      setProcessingSteps(prev => [...prev, step]);
    });

    newSocket.on('typing_start', () => {
      setProcessingSteps([]);
    });

    newSocket.on('typing_end', () => {
      setTimeout(() => {
        setProcessingSteps([]);
      }, 2000); // Clear steps after 2 seconds
    });
    
    setSocket(newSocket);
  };

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setConnected(data.claude_available);
      if (data.active_connections !== undefined) {
        setConnectionStats({
          active_connections: data.active_connections,
          active_sessions: data.active_sessions
        });
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setConnected(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading || !socket) {
      console.log('⚠️ [TRACE] Send message blocked:', {
        hasInput: !!input.trim(),
        loading: loading,
        hasSocket: !!socket
      });
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    console.log('📤 [TRACE] Sending message via socket:', {
      messageId: userMessage.id,
      contentLength: userMessage.content.length,
      sessionId: sessionId,
      timestamp: new Date().toISOString()
    });

    setInput('');
    setLoading(true);
    setCurrentStreamingContent('');

    // Send message via socket
    socket.emit('send_message', {
      message: userMessage.content,
      sessionId: sessionId,
      systemPrompt: settings.systemPrompt || undefined,
      maxTurns: settings.maxTurns,
      allowedTools: settings.allowedTools,
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId('');
    setCurrentStreamingContent('');
    if (socket) {
      socket.emit('create_session');
    }
  };

  const loadSession = (session: Session) => {
    if (socket) {
      socket.emit('load_session', session.id);
      setShowSidebar(false);
    }
  };

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/sessions`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const exportConversation = async (format: 'markdown' | 'json' = 'markdown') => {
    try {
      const response = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, format })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `claude-chat-${Date.now()}.${format === 'json' ? 'json' : 'md'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !socket) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });

      const result: FileUploadResult = await response.json();
      
      if (result.success) {
        // Trigger file analysis
        socket.emit('analyze_file', {
          content: result.content,
          filename: result.filename,
          prompt: 'Please analyze this file and provide insights about its structure, purpose, and any potential improvements.'
        });
        setShowFileUpload(false);
      } else {
        console.error('File upload failed:', result);
      }
    } catch (error) {
      console.error('File upload error:', error);
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const formatMetadata = (message: Message) => {
    const parts = [];
    if (message.cost !== undefined) parts.push(`$${message.cost.toFixed(4)}`);
    if (message.duration !== undefined) parts.push(`${message.duration.toFixed(0)}ms`);
    if (message.turns !== undefined) parts.push(`${message.turns} turns`);
    return parts.length > 0 ? `(${parts.join(' • ')})` : '';
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getStepIcon = (stepType: string) => {
    const iconStyle = { 
      width: '14px', 
      height: '14px', 
      borderRadius: '50%',
      display: 'inline-block',
      border: '2px solid transparent'
    };

    switch (stepType) {
      case 'initializing':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.accent, 
          animation: 'pulse 1s infinite',
          border: `2px solid ${colors.accentLight}`
        }}></div>;
      case 'connecting':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.warning,
          border: `2px solid ${colors.warningLight}`,
          animation: 'pulse 0.8s infinite'
        }}></div>;
      case 'thinking':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.accent, 
          animation: 'pulse 1.5s infinite',
          border: `2px solid ${colors.accentLight}`,
          boxShadow: `0 0 4px ${colors.accent}`
        }}></div>;
      case 'tool_use':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.success,
          border: `2px solid ${colors.successLight}`,
          animation: 'pulse 0.6s infinite'
        }}></div>;
      case 'tool_result':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.success,
          border: `2px solid ${colors.successLight}`
        }}></div>;
      case 'result':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.statusSuccess,
          border: `2px solid ${colors.successLight}`,
          boxShadow: `0 0 6px ${colors.success}`
        }}></div>;
      case 'finalizing':
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.statusSuccess,
          border: `2px solid ${colors.successLight}`,
          animation: 'pulse 0.5s infinite'
        }}></div>;
      default:
        return <div style={{ 
          ...iconStyle, 
          backgroundColor: colors.textTertiary,
          border: `2px solid ${colors.borderLight}`
        }}></div>;
    }
  };

  const renderStepData = (data: any) => {
    if (!data || typeof data !== 'object') return null;

    return (
      <div className="text-xs mt-2 space-y-1" style={{ color: colors.textTertiary }}>
        {/* Initialization Data */}
        {data.type === 'initialization' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Initialization Details:</div>
            <div>• Prompt size: <span style={{ color: colors.textSecondary }}>{data.promptLength} characters</span></div>
            <div>• Max turns: <span style={{ color: colors.textSecondary }}>{data.maxTurns}</span></div>
            <div>• Allowed tools: <span style={{ color: colors.textSecondary }}>{data.allowedTools?.length || 0} tools</span></div>
            <div>• Session: <span style={{ color: colors.textSecondary }}>{data.sessionInfo}</span></div>
          </>
        )}

        {/* Connection Data */}
        {data.type === 'connection' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Connection Details:</div>
            <div>• Endpoint: <span style={{ color: colors.textSecondary }}>{data.apiEndpoint}</span></div>
            <div>• Auth: <span style={{ color: colors.success }}>{data.authentication}</span></div>
            <div>• Request size: <span style={{ color: colors.textSecondary }}>{data.requestSize}</span></div>
          </>
        )}

        {/* Tool Use Data */}
        {data.type === 'tool_use' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Tool Execution:</div>
            <div>• Tool: <span style={{ color: colors.accent }}>{data.toolName}</span></div>
            <div>• ID: <span style={{ color: colors.textSecondary }}>{data.toolId?.slice(0, 12)}...</span></div>
            {data.inputSummary && (
              <div>• Input: <span style={{ color: colors.textSecondary }}>{data.inputSummary}</span></div>
            )}
            {data.expectedOutput && (
              <div>• Expected: <span style={{ color: colors.textSecondary }}>{data.expectedOutput}</span></div>
            )}
            {data.toolDescription && (
              <div className="mt-1 italic">"{data.toolDescription}"</div>
            )}
          </>
        )}

        {/* Tool Result Data */}
        {data.type === 'tool_result' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Tool Result:</div>
            <div>• Status: <span style={{ color: data.executionStatus === 'success' ? colors.success : colors.error }}>
              {data.executionStatus}</span></div>
            <div>• Tool ID: <span style={{ color: colors.textSecondary }}>{data.toolUseId?.slice(0, 12)}...</span></div>
            {data.contentLength && (
              <div>• Output size: <span style={{ color: colors.textSecondary }}>{data.contentLength} chars</span></div>
            )}
            {data.contentType && (
              <div>• Content type: <span style={{ color: colors.textSecondary }}>{data.contentType}</span></div>
            )}
            {data.outputSummary && (
              <div>• Summary: <span style={{ color: colors.textSecondary }}>{data.outputSummary}</span></div>
            )}
            {data.errorDetails && (
              <div>• Error: <span style={{ color: colors.error }}>{data.errorDetails.substring(0, 100)}...</span></div>
            )}
          </>
        )}

        {/* Result Data */}
        {data.type === 'result' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Processing Complete:</div>
            <div>• Status: <span style={{ color: data.isError ? colors.error : colors.success }}>
              {data.isError ? 'Failed' : 'Success'}</span></div>
            {data.duration && (
              <div>• Duration: <span style={{ color: colors.textSecondary }}>{data.duration}ms</span></div>
            )}
            {data.cost && (
              <div>• Cost: <span style={{ color: colors.textSecondary }}>${data.cost.toFixed(4)}</span></div>
            )}
            {data.turns && (
              <div>• Turns: <span style={{ color: colors.textSecondary }}>{data.turns}</span></div>
            )}
            
            {/* Token Usage */}
            {(data.inputTokens || data.outputTokens) && (
              <>
                <div className="font-medium mt-2 mb-1" style={{ color: colors.textSecondary }}>Token Usage:</div>
                {data.inputTokens && (
                  <div>• Input: <span style={{ color: colors.textSecondary }}>{data.inputTokens.toLocaleString()} tokens</span></div>
                )}
                {data.outputTokens && (
                  <div>• Output: <span style={{ color: colors.textSecondary }}>{data.outputTokens.toLocaleString()} tokens</span></div>
                )}
                {data.cacheReads && (
                  <div>• Cache reads: <span style={{ color: colors.success }}>{data.cacheReads.toLocaleString()} tokens</span></div>
                )}
                {data.cacheWrites && (
                  <div>• Cache writes: <span style={{ color: colors.warning }}>{data.cacheWrites.toLocaleString()} tokens</span></div>
                )}
              </>
            )}

            {/* Response Analysis */}
            {data.responseLength && (
              <>
                <div className="font-medium mt-2 mb-1" style={{ color: colors.textSecondary }}>Response Analysis:</div>
                <div>• Length: <span style={{ color: colors.textSecondary }}>{data.responseLength} characters</span></div>
                <div>• Words: <span style={{ color: colors.textSecondary }}>{data.responseWords?.toLocaleString()}</span></div>
                <div>• Lines: <span style={{ color: colors.textSecondary }}>{data.responseLines}</span></div>
                <div>• Has code: <span style={{ color: data.hasCodeBlocks ? colors.success : colors.textTertiary }}>
                  {data.hasCodeBlocks ? 'Yes' : 'No'}</span></div>
                <div>• Markdown: <span style={{ color: data.hasMarkdown ? colors.success : colors.textTertiary }}>
                  {data.hasMarkdown ? 'Yes' : 'No'}</span></div>
              </>
            )}

            {/* Error Details */}
            {data.isError && (
              <>
                <div className="font-medium mt-2 mb-1" style={{ color: colors.error }}>Error Details:</div>
                <div>• Type: <span style={{ color: colors.error }}>{data.errorType}</span></div>
                <div>• Message: <span style={{ color: colors.error }}>{data.errorMessage}</span></div>
              </>
            )}
          </>
        )}

        {/* Thinking Data */}
        {data.type === 'thinking' && (
          <>
            <div className="font-medium mb-1" style={{ color: colors.textSecondary }}>Cognitive Processing:</div>
            <div>• Load: <span style={{ color: colors.accent }}>{data.cognitiveLoad}</span></div>
            <div>• Phase: <span style={{ color: colors.textSecondary }}>{data.analysisPhase}</span></div>
            <div>• Strategy: <span style={{ color: colors.textSecondary }}>
              {data.strategizing ? 'Planning response approach' : 'Executing plan'}</span></div>
          </>
        )}

        {/* Message ID and Timestamp */}
        {data.messageId && (
          <div className="mt-2 pt-1 border-t" style={{ borderTopColor: colors.borderLight }}>
            <div>• Message ID: <span style={{ color: colors.textTertiary }}>{data.messageId}</span></div>
          </div>
        )}
      </div>
    );
  };

  useEffect(() => {
    if (showSidebar) {
      loadSessions();
    }
  }, [showSidebar]);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: colors.background }}>
      {/* Header */}
      <div className="p-4 shadow-sm" style={{ backgroundColor: colors.surface, borderBottom: `1px solid ${colors.border}` }}>
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-semibold" style={{ color: colors.textPrimary }}>Claude Code Chat</h1>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full shadow-sm`} style={{
                backgroundColor: connected === null ? colors.statusWarning : 
                                connected ? colors.statusSuccess : colors.statusError
              }}></div>
              <span className="text-sm font-medium" style={{ color: colors.textSecondary }}>
                {connected === null ? 'Checking...' : 
                 connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <HeaderButton
              onClick={() => setShowSidebar(!showSidebar)}
              active={showSidebar}
            >
              Sessions
            </HeaderButton>
            <HeaderButton
              onClick={() => setShowSettings(!showSettings)}
              active={showSettings}
            >
              Settings
            </HeaderButton>
            <HeaderButton
              onClick={() => setShowFileUpload(!showFileUpload)}
              active={showFileUpload}
              variant="success"
            >
              Upload
            </HeaderButton>
            <HeaderButton
              onClick={() => exportConversation('markdown')}
            >
              Export
            </HeaderButton>
            <HeaderButton
              onClick={clearChat}
              variant="danger"
            >
              Clear Chat
            </HeaderButton>
          </div>
        </div>
      </div>

      {/* Sidebar for Sessions */}
      {showSidebar && (
        <div className="fixed inset-0 z-50 flex">
          <div 
            className="absolute inset-0 transition-opacity duration-200"
            style={{ backgroundColor: colors.overlay }}
            onClick={() => setShowSidebar(false)}
          ></div>
          <div 
            className="relative w-80 h-full overflow-y-auto shadow-xl"
            style={{ backgroundColor: colors.surface, borderRight: `1px solid ${colors.border}` }}
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold" style={{ color: colors.textPrimary }}>Sessions</h2>
                <button
                  onClick={() => setShowSidebar(false)}
                  className="text-lg font-bold w-8 h-8 rounded-full transition-colors hover:bg-opacity-10"
                  style={{ 
                    color: colors.textTertiary,
                    backgroundColor: 'transparent'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = colors.hover;
                    e.currentTarget.style.color = colors.textSecondary;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = colors.textTertiary;
                  }}
                >
                  ×
                </button>
              </div>
              <HeaderButton
                onClick={() => {
                  if (socket) {
                    socket.emit('create_session');
                  }
                }}
                variant="success"
                style={{ width: '100%', marginBottom: '1rem' }}
              >
                New Session
              </HeaderButton>
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-3 rounded-lg cursor-pointer transition-all duration-200 border"
                    style={{ 
                      backgroundColor: sessionId === session.id ? colors.accentLight : colors.surfaceSecondary,
                      color: colors.textPrimary,
                      borderColor: sessionId === session.id ? colors.accent : colors.borderLight,
                      boxShadow: sessionId === session.id ? `0 2px 4px ${colors.overlayLight}` : 'none'
                    }}
                    onMouseEnter={(e) => {
                      if (sessionId !== session.id) {
                        e.currentTarget.style.backgroundColor = colors.hover;
                        e.currentTarget.style.borderColor = colors.border;
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (sessionId !== session.id) {
                        e.currentTarget.style.backgroundColor = colors.surfaceSecondary;
                        e.currentTarget.style.borderColor = colors.borderLight;
                      }
                    }}
                    onClick={() => loadSession(session)}
                  >
                    <div className="font-medium text-sm truncate">
                      {session.title}
                    </div>
                    <div className="text-xs mt-1" style={{ color: colors.textTertiary }}>
                      {session.messageCount} messages • {formatTimestamp(session.lastActivity)}
                    </div>
                  </div>
                ))}
                {sessions.length === 0 && (
                  <div className="text-center py-8" style={{ color: colors.textTertiary }}>
                    <div className="text-sm">No sessions yet</div>
                    <div className="text-xs mt-1">Create a new session to get started</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 transition-opacity duration-200"
            style={{ backgroundColor: colors.overlay }}
            onClick={() => setShowSettings(false)}
          ></div>
          <div 
            className="relative w-full max-w-md p-6 rounded-xl shadow-2xl"
            style={{ backgroundColor: colors.surface, border: `1px solid ${colors.border}` }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold" style={{ color: colors.textPrimary }}>Settings</h2>
              <button
                onClick={() => setShowSettings(false)}
                className="text-lg font-bold w-8 h-8 rounded-full transition-colors"
                style={{ 
                  color: colors.textTertiary,
                  backgroundColor: 'transparent'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = colors.hover;
                  e.currentTarget.style.color = colors.textSecondary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = colors.textTertiary;
                }}
              >
                ×
              </button>
            </div>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: colors.textPrimary }}>
                  System Prompt
                </label>
                <textarea
                  value={settings.systemPrompt}
                  onChange={(e) => setSettings(prev => ({ ...prev, systemPrompt: e.target.value }))}
                  placeholder="Optional system prompt to customize Claude's behavior..."
                  className="w-full p-3 rounded-lg border resize-none transition-all duration-200 focus:outline-none"
                  style={{ 
                    backgroundColor: colors.surfaceSecondary,
                    borderColor: colors.border,
                    color: colors.textPrimary
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = colors.borderFocus;
                    e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.accentLight}`;
                    e.currentTarget.style.backgroundColor = colors.surface;
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = colors.border;
                    e.currentTarget.style.boxShadow = 'none';
                    e.currentTarget.style.backgroundColor = colors.surfaceSecondary;
                  }}
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-3" style={{ color: colors.textPrimary }}>
                  Max Turns: <span style={{ color: colors.accent }}>{settings.maxTurns}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={settings.maxTurns}
                  onChange={(e) => setSettings(prev => ({ ...prev, maxTurns: parseInt(e.target.value) }))}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, ${colors.accent} 0%, ${colors.accent} ${(settings.maxTurns - 1) * 11.11}%, ${colors.borderLight} ${(settings.maxTurns - 1) * 11.11}%, ${colors.borderLight} 100%)`
                  }}
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg" style={{ backgroundColor: colors.surfaceSecondary }}>
                <span className="text-sm font-medium" style={{ color: colors.textPrimary }}>Streaming Enabled</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.streamingEnabled}
                    onChange={(e) => setSettings(prev => ({ ...prev, streamingEnabled: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div 
                    className="w-11 h-6 rounded-full transition-colors duration-200"
                    style={{ 
                      backgroundColor: settings.streamingEnabled ? colors.accent : colors.border 
                    }}
                  >
                    <div 
                      className="w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-200 mt-0.5"
                      style={{ 
                        marginLeft: settings.streamingEnabled ? '1.25rem' : '0.125rem'
                      }}
                    ></div>
                  </div>
                </label>
              </div>
              <div className="text-xs p-3 rounded-lg" style={{ 
                color: colors.textTertiary,
                backgroundColor: colors.surfaceTertiary 
              }}>
                Active Connections: {connectionStats.active_connections} | Active Sessions: {connectionStats.active_sessions}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File Upload Modal */}
      {showFileUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 transition-opacity duration-200"
            style={{ backgroundColor: colors.overlay }}
            onClick={() => setShowFileUpload(false)}
          ></div>
          <div 
            className="relative w-full max-w-md p-6 rounded-xl shadow-2xl"
            style={{ backgroundColor: colors.surface, border: `1px solid ${colors.border}` }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold" style={{ color: colors.textPrimary }}>Upload File</h2>
              <button
                onClick={() => setShowFileUpload(false)}
                className="text-lg font-bold w-8 h-8 rounded-full transition-colors"
                style={{ 
                  color: colors.textTertiary,
                  backgroundColor: 'transparent'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = colors.hover;
                  e.currentTarget.style.color = colors.textSecondary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = colors.textTertiary;
                }}
              >
                ×
              </button>
            </div>
            <div className="space-y-6">
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  accept=".js,.ts,.jsx,.tsx,.py,.java,.cpp,.c,.h,.css,.html,.json,.xml,.yaml,.yml,.md,.txt,.php,.rb,.go,.rs,.swift,.kt,.scala,.sql"
                  className="w-full p-4 rounded-lg border-2 border-dashed transition-all duration-200"
                  style={{ 
                    backgroundColor: colors.surfaceSecondary,
                    borderColor: colors.border,
                    color: colors.textPrimary
                  }}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.borderColor = colors.accent;
                    e.currentTarget.style.backgroundColor = colors.accentLight;
                  }}
                  onDragLeave={(e) => {
                    e.currentTarget.style.borderColor = colors.border;
                    e.currentTarget.style.backgroundColor = colors.surfaceSecondary;
                  }}
                  onDrop={(e) => {
                    e.currentTarget.style.borderColor = colors.border;
                    e.currentTarget.style.backgroundColor = colors.surfaceSecondary;
                  }}
                />
              </div>
              <div className="text-xs p-3 rounded-lg" style={{ 
                color: colors.textTertiary,
                backgroundColor: colors.surfaceTertiary 
              }}>
                <strong>Supported:</strong> Text files, code files (JS, TS, Python, etc.), max 10MB
              </div>
              {loading && (
                <div className="text-center p-4 rounded-lg" style={{ backgroundColor: colors.accentLight }}>
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 rounded-full animate-spin border-2 border-transparent" style={{ 
                      borderTopColor: colors.accent,
                      borderRightColor: colors.accent
                    }}></div>
                    <span className="text-sm font-medium" style={{ color: colors.accent }}>
                      Uploading and analyzing file...
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="mb-4">
                <div className="w-16 h-16 mx-auto rounded-full flex items-center justify-center" style={{ backgroundColor: colors.accentLight }}>
                  <span className="text-2xl">💬</span>
                </div>
              </div>
              <p className="text-lg mb-2 font-medium" style={{ color: colors.textPrimary }}>Welcome to Claude Code Chat</p>
              <p className="text-sm" style={{ color: colors.textTertiary }}>Start a conversation by typing a message below.</p>
            </div>
          )}
          
          {messages.map((message) => {
            console.log('🎨 [TRACE] Rendering message in UI:', {
              messageId: message.id,
              type: message.type,
              contentLength: message.content?.length,
              isError: message.is_error
            });
            
            return (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-xl px-5 py-3 shadow-sm ${message.is_error ? 'border-l-4' : ''}`}
                style={{
                  backgroundColor: message.type === 'user' 
                    ? colors.accent 
                    : message.is_error 
                      ? colors.errorLight 
                      : colors.surface,
                  color: message.type === 'user' ? colors.surface : colors.textPrimary,
                  border: message.type === 'assistant' ? `1px solid ${colors.border}` : 'none',
                  borderLeftColor: message.is_error ? colors.error : undefined,
                  boxShadow: message.type === 'user' 
                    ? `0 2px 8px ${colors.overlayLight}` 
                    : `0 1px 3px ${colors.overlayLight}`
                }}
              >
                {message.type === 'assistant' ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={MarkdownComponents}
                  >
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                )}
                {message.type === 'assistant' && formatMetadata(message) && (
                  <div className="text-xs mt-3 pt-2 border-t" style={{ 
                    color: colors.textTertiary,
                    borderTopColor: colors.borderLight
                  }}>
                    {formatMetadata(message)}
                  </div>
                )}
              </div>
            </div>
            );
          })}
          
          {/* Processing Steps Display */}
          {processingSteps.length > 0 && (
            <div className="flex justify-start">
              <div 
                className="max-w-3xl rounded-xl px-5 py-3 shadow-sm border"
                style={{
                  backgroundColor: colors.surfaceSecondary,
                  borderColor: colors.accent,
                  color: colors.textSecondary
                }}
              >
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-3 h-3 rounded-full animate-pulse" style={{ backgroundColor: colors.accent }}></div>
                    <span className="text-sm font-medium" style={{ color: colors.accent }}>
                      Processing your request...
                    </span>
                  </div>
                  
                  {processingSteps.map((step, index) => (
                    <div key={index} className="flex items-start space-x-3 py-2 px-2 rounded-lg" 
                         style={{ backgroundColor: index === processingSteps.length - 1 ? colors.accentLight : 'transparent' }}>
                      <div className="flex-shrink-0 mt-1">
                        {getStepIcon(step.step)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium" style={{ color: colors.textPrimary }}>
                            {step.message}
                          </div>
                          <div className="text-xs ml-2 flex-shrink-0" style={{ color: colors.textTertiary }}>
                            {new Date(step.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                        
                        {step.data && (
                          <div className="mt-1">
                            {renderStepData(step.data)}
                          </div>
                        )}
                        
                        {/* Progress indicator for current step */}
                        {index === processingSteps.length - 1 && (
                          <div className="mt-2">
                            <div className="w-full bg-gray-200 rounded-full h-1">
                              <div className="h-1 rounded-full animate-pulse" 
                                   style={{ 
                                     backgroundColor: colors.accent,
                                     width: '70%',
                                     animation: 'pulse 1s infinite'
                                   }}></div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {currentStreamingContent && (() => {
            console.log('🌊 [TRACE] Rendering streaming content in UI:', {
              contentLength: currentStreamingContent.length,
              preview: currentStreamingContent.substring(0, 50) + '...'
            });
            
            return (
            <div className="flex justify-start">
              <div
                className="max-w-3xl rounded-xl px-5 py-3 shadow-sm border relative"
                style={{
                  backgroundColor: colors.surface,
                  color: colors.textPrimary,
                  borderColor: colors.accent,
                  boxShadow: `0 1px 3px ${colors.overlayLight}, 0 0 0 1px ${colors.accentLight}`
                }}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={MarkdownComponents}
                >
                  {currentStreamingContent}
                </ReactMarkdown>
                <div className="flex items-center mt-3 pt-2 border-t" style={{ borderTopColor: colors.borderLight }}>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.accent }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.accent, animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.accent, animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-xs ml-3 font-medium" style={{ color: colors.accent }}>
                    Claude is typing...
                  </span>
                </div>
              </div>
            </div>
            );
          })()}
          
          {loading && !currentStreamingContent && (
            <div className="flex justify-start">
              <div className="rounded-xl px-5 py-3 shadow-sm border" style={{ 
                backgroundColor: colors.surface, 
                borderColor: colors.border,
                boxShadow: `0 1px 3px ${colors.overlayLight}`
              }}>
                <div className="flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.warning }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.warning, animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: colors.warning, animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-sm font-medium" style={{ color: colors.textSecondary }}>Claude is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="p-4 shadow-sm" style={{ backgroundColor: colors.surface, borderTop: `1px solid ${colors.border}` }}>
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              className="flex-1 resize-none rounded-xl px-4 py-3 focus:outline-none transition-all duration-200"
              style={{ 
                border: `2px solid ${colors.border}`,
                backgroundColor: colors.surfaceSecondary,
                color: colors.textPrimary,
                minHeight: '52px'
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = colors.borderFocus;
                e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.accentLight}`;
                e.currentTarget.style.backgroundColor = colors.surface;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.backgroundColor = colors.surfaceSecondary;
              }}
              rows={1}
              disabled={loading || connected === false}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading || connected === false}
              className="px-6 py-3 rounded-xl transition-all duration-200 font-semibold focus:outline-none min-w-[80px]"
              style={{ 
                backgroundColor: !input.trim() || loading || connected === false 
                  ? colors.disabled 
                  : colors.success,
                color: colors.surface,
                cursor: !input.trim() || loading || connected === false ? 'not-allowed' : 'pointer',
                boxShadow: !input.trim() || loading || connected === false 
                  ? 'none' 
                  : `0 2px 4px ${colors.overlayLight}`
              }}
              onMouseEnter={(e) => {
                if (input.trim() && !loading && connected !== false) {
                  e.currentTarget.style.backgroundColor = colors.successHover;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = `0 4px 8px ${colors.overlayLight}`;
                }
              }}
              onMouseLeave={(e) => {
                if (input.trim() && !loading && connected !== false) {
                  e.currentTarget.style.backgroundColor = colors.success;
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = `0 2px 4px ${colors.overlayLight}`;
                }
              }}
              onFocus={(e) => {
                if (input.trim() && !loading && connected !== false) {
                  e.currentTarget.style.outline = 'none';
                  e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.successLight}`;
                }
              }}
              onBlur={(e) => {
                if (input.trim() && !loading && connected !== false) {
                  e.currentTarget.style.boxShadow = `0 2px 4px ${colors.overlayLight}`;
                }
              }}
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
          {sessionId && (
            <div className="text-xs mt-3 flex items-center space-x-2" style={{ color: colors.textTertiary }}>
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors.statusSuccess }}></span>
              <span>Session: <span className="font-mono">{sessionId.slice(0, 8)}...</span></span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
