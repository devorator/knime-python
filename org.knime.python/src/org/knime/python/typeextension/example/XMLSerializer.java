package org.knime.python.typeextension.example;

import java.io.IOException;

import javax.xml.parsers.ParserConfigurationException;
import javax.xml.stream.XMLStreamException;

import org.knime.core.data.DataCell;
import org.knime.core.data.xml.XMLCell;
import org.knime.core.data.xml.XMLCellFactory;
import org.knime.core.data.xml.XMLValue;
import org.knime.python.typeextension.Serializer;
import org.xml.sax.SAXException;

public class XMLSerializer extends Serializer<XMLValue> {
	
	public XMLSerializer() {
		super(XMLCell.TYPE, XMLValue.class);
	}

	@Override
	public byte[] serialize(XMLValue value) throws IOException {
		return value.toString().getBytes();
	}

	@Override
	public DataCell deserialize(byte[] bytes) throws IOException {
		try {
			return XMLCellFactory.create(new String(bytes));
		} catch (ParserConfigurationException | SAXException
				| XMLStreamException e) {
			throw new IOException(e.getMessage(), e);
		}
	}

}
