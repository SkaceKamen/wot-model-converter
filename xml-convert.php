<?php
class wotxmlreader
{
	const PACKED_HEADER = 0x62a14e45;
	
	
	private $file;
	
	public function __construct() {
		
	}
	public function getXML($filename) {
		$this->file = fopen($filename, 'rb');
		$this->checkHeader();
		
		$dictionary = $this->readDictionary();
		$root = new SimpleXMLElement('<root></root>');
		$this->readElement($dictionary, $root);
		
		return $root;
	}
	
	private function unpack($format, $data) {
		$result = unpack($format, $data);
		if (!isset($result[1]))
			throw new Exception("Unpack failed.");
		return $result[1];
	}
	
	private function readElement($dictionary, $element) {
		$children_count = $this->unpack('v', fread($this->file, 2));

		$descriptor = $this->readDataDescriptor();
		$children = $this->readElementDescriptors($children_count);
		
		$offset = $this->readData($dictionary, $element, 0, $descriptor);
		
		foreach($children as $child) {
			$node = $element->addChild($dictionary[$child->name_index]);
			$offset = $this->readData($dictionary, $node, $offset, $child->descriptor);
		}
	}
	
	private function readData($dictionary, $element, $offset, $descriptor) {
		$length = $descriptor->end - $offset;
		
		switch ($descriptor->type) {
			case 0: $this->readElement($dictionary, $element); break;
			case 1: $element[0] = $this->readString($length); break;
			case 2: $element[0] = $this->readNumber($length); break;
			case 3: $element[0] = $this->readFloat($length); break;
			case 4: $element[0] = $this->readBoolean($length); break;
			case 5: $element[0] = $this->readBase64($length); break;
			default:
				throw new Exception("Unknown element type '{$descriptor->type}'.");
		}

		return $descriptor->end;
	}
	
	private function readString($length) {
		if ($length == 0)
			return null;
		
		return fread($this->file, $length);
	}
	
	private function readNumber($length) {
		if ($length == 0)
			return 0;
		
		$data = fread($this->file, $length);
		switch($length) {
			case 1: return $this->unpack('c', $data);
			case 2: return $this->unpack('v', $data);
			case 4: return $this->unpack('V', $data);
			default:
				throw new Exception("Unknown number size: $length.");
		}
	}
	
	private function readFloat($length) {
		$n = (int)($length / 4);
		
		$res = '';
		for($i = 0; $i < $n; $i++) {
			if ($i != 0)
				$res .= ' ';
			
			$res .= $this->unpack('f', fread($this->file, 4));
		}
		
		return $res;
	}
	
	private function readBase64($length) {
		return base64_encode(fread($this->file, $length));
	}
	
	private function readBoolean($length) {
		if ($length == 0)
			return false;

		if ($length == 1) {
			$b = $this->unpack('C', fread($this->file, 1));
			if ($b == 1)
				return true;
			return false;
		} else {
			throw new Exception("Boolean with lenght > 1 ($length).");
		}
	}
	

	private function readDataDescriptor() {
		$data = fread($this->file, 4);
		if ($data) {
			$end_type = $this->unpack('V', $data);
			
			$descriptor = (object)array(
				'end' => $end_type & 0x0fffffff,
				'type' => ($end_type >> 28) + 0,
				'address' => ftell($this->file)
			);
			
			return $descriptor;
		} else {
			throw new Exception("Failed to read data descriptor");
		}
	}
	
	private function readElementDescriptors($count) {
		$descriptors = array();
		
		for($i = 0; $i < $count; $i++) {
			$data = fread($this->file, 2);
			
			if ($data) {
				$name_index = $this->unpack('v', $data);
				$descriptor = $this->readDataDescriptor();
				$descriptors[] = (object)array(
					'name_index' => $name_index,
					'descriptor' => $descriptor
				);
			} else {
				throw new Exception('Failed to read element descriptors');
			}
		}
		
		return $descriptors;
	}
	
	private function checkHeader() {
		fseek($this->file, 0, SEEK_SET);
		$header = $this->unpack('I', fread($this->file, 4));
		if ($header != self::PACKED_HEADER) {
			throw new Exception("Not a World of Tanks XML compressed file");
		}
	}
	
	private function readDictionary() {
		fseek($this->file, 5, SEEK_SET);
		
		$dictionary = array();
		while($string = $this->readASCIIZ()) {
			$dictionary[] = $string;
		}
		
		return $dictionary;
	}
	
	private function readASCIIZ() {
		$string = '';
		while(true) {
			$char = fread($this->file, 1);
			if (ord($char) == 0)
				break;
			$string .= $char;
		}
		return $string;
	}
}

if (count($argv) != 3) {
	echo "USAGE:\n";
	echo "\txml-conver.php INPUT_XML OUTPUT_XML|-\n";
	exit(1);
}

try {
	$reader = new wotxmlreader();
	$xml = $reader->getXML($argv[1]);
} catch (Exception $e) {
	echo "Error occured:\n";
	echo $e->getMessage();
	echo "\n";
	exit(2);
}

if ($argv[2] == '-')
	die($xml->asXML());
else
	file_put_contents($argv[2], $xml->asXML());